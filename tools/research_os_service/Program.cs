using System.Diagnostics;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

const string ServiceName = "ResearchOSService";

var host = Host.CreateDefaultBuilder(args)
    .UseWindowsService(options => options.ServiceName = ServiceName)
    .ConfigureServices(services => services.AddHostedService<ResearchOsApiWorker>())
    .Build();

await host.RunAsync();

sealed class ResearchOsApiWorker : BackgroundService
{
    private readonly ILogger<ResearchOsApiWorker> _logger;
    private readonly SemaphoreSlim _processStopLock = new(1, 1);
    private Process? _process;

    public ResearchOsApiWorker(ILogger<ResearchOsApiWorker> logger)
    {
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        var repoRoot = ResolveRepoRoot();
        var dataDir = Environment.GetEnvironmentVariable("RESEARCH_OS_DATA_DIR")
            ?? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData), "ResearchOS");
        var pythonExe = ResolvePython(repoRoot);
        var apiDir = Path.Combine(repoRoot, "tools", "research_os_api");
        var serverPath = Path.Combine(apiDir, "render_server.py");

        if (!File.Exists(serverPath))
        {
            throw new FileNotFoundException("Research OS API entrypoint not found", serverPath);
        }

        Directory.CreateDirectory(dataDir);
        Directory.CreateDirectory(Path.Combine(dataDir, "sessions"));
        Directory.CreateDirectory(Path.Combine(dataDir, "database"));
        Directory.CreateDirectory(Path.Combine(dataDir, "artifacts"));
        Directory.CreateDirectory(Path.Combine(dataDir, "logs"));

        var stdoutPath = Path.Combine(dataDir, "logs", "service-api.out.log");
        var stderrPath = Path.Combine(dataDir, "logs", "service-api.err.log");

        _logger.LogInformation("Research OS root: {RepoRoot}", repoRoot);
        _logger.LogInformation("Research OS Python: {PythonExe}", pythonExe);
        _logger.LogInformation("Research OS data: {DataDir}", dataDir);

        var startInfo = new ProcessStartInfo
        {
            FileName = pythonExe,
            Arguments = Quote(serverPath),
            WorkingDirectory = apiDir,
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
        };

        startInfo.Environment["RESEARCH_OS_DATA_DIR"] = dataDir;
        startInfo.Environment["RESEARCH_OS_CONVERSATION_STORE"] = Path.Combine(dataDir, "sessions", "conversations.json");
        startInfo.Environment["RESEARCH_OS_API_HOST"] = Environment.GetEnvironmentVariable("RESEARCH_OS_API_HOST") ?? "127.0.0.1";
        startInfo.Environment["RESEARCH_OS_API_PORT"] = Environment.GetEnvironmentVariable("RESEARCH_OS_API_PORT") ?? "8787";
        startInfo.Environment["HOST"] = startInfo.Environment["RESEARCH_OS_API_HOST"]!;
        startInfo.Environment["PORT"] = startInfo.Environment["RESEARCH_OS_API_PORT"]!;

        _process = new Process { StartInfo = startInfo, EnableRaisingEvents = true };
        if (!_process.Start())
        {
            throw new InvalidOperationException("Failed to start Research OS API process.");
        }

        _logger.LogInformation("Research OS API started with PID {Pid}", _process.Id);

        var stdoutTask = PumpAsync(_process.StandardOutput, stdoutPath, stoppingToken);
        var stderrTask = PumpAsync(_process.StandardError, stderrPath, stoppingToken);
        var exitTask = _process.WaitForExitAsync(stoppingToken);

        try
        {
            await exitTask;
        }
        catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
        {
            await StopChildProcessAsync(CancellationToken.None);
            return;
        }
        finally
        {
            if (stoppingToken.IsCancellationRequested)
            {
                await StopChildProcessAsync(CancellationToken.None);
            }

            await Task.WhenAll(IgnoreCancellation(stdoutTask), IgnoreCancellation(stderrTask));
        }

        if (!stoppingToken.IsCancellationRequested)
        {
            throw new InvalidOperationException($"Research OS API exited unexpectedly with code {_process?.ExitCode}.");
        }
    }

    public override async Task StopAsync(CancellationToken cancellationToken)
    {
        await StopChildProcessAsync(cancellationToken);
        await base.StopAsync(cancellationToken);
        await StopChildProcessAsync(CancellationToken.None);
    }

    public override void Dispose()
    {
        try
        {
            StopChildProcessAsync(CancellationToken.None).GetAwaiter().GetResult();
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to terminate Research OS API during worker disposal");
        }
        finally
        {
            _processStopLock.Dispose();
            base.Dispose();
        }
    }

    private async Task StopChildProcessAsync(CancellationToken cancellationToken)
    {
        await _processStopLock.WaitAsync(cancellationToken);
        try
        {
            var process = _process;
            if (process is null)
            {
                return;
            }

            try
            {
                if (!process.HasExited)
                {
                    _logger.LogInformation("Stopping Research OS API PID {Pid} and its process tree", process.Id);
                    process.Kill(entireProcessTree: true);

                    using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
                    timeout.CancelAfter(TimeSpan.FromSeconds(10));
                    await process.WaitForExitAsync(timeout.Token);
                }
            }
            catch (OperationCanceledException)
            {
                _logger.LogWarning("Timed out waiting for Research OS API PID {Pid} to exit", SafePid(process));
                try { process.Kill(entireProcessTree: true); } catch { }
            }
            catch (InvalidOperationException)
            {
                // The process already exited between HasExited and Kill/WaitForExitAsync.
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Failed to stop Research OS API child process cleanly");
                try { process.Kill(entireProcessTree: true); } catch { }
            }
            finally
            {
                try { process.Dispose(); } catch { }
                if (ReferenceEquals(_process, process))
                {
                    _process = null;
                }
            }
        }
        finally
        {
            _processStopLock.Release();
        }
    }

    private static int SafePid(Process process)
    {
        try { return process.Id; }
        catch { return -1; }
    }

    private static string ResolveRepoRoot()
    {
        var configured = Environment.GetEnvironmentVariable("RESEARCH_OS_REPO_ROOT");
        if (!string.IsNullOrWhiteSpace(configured) && Directory.Exists(configured))
        {
            return Path.GetFullPath(configured);
        }

        var packagedRoot = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", ".."));
        var packagedEntrypoint = Path.Combine(packagedRoot, "tools", "research_os_api", "render_server.py");
        if (File.Exists(packagedEntrypoint))
        {
            return packagedRoot;
        }

        throw new InvalidOperationException(
            $"RESEARCH_OS_REPO_ROOT is not configured and packaged root could not be resolved from {AppContext.BaseDirectory}.");
    }

    private static string ResolvePython(string repoRoot)
    {
        var configured = Environment.GetEnvironmentVariable("RESEARCH_OS_PYTHON_EXE");
        if (!string.IsNullOrWhiteSpace(configured) && File.Exists(configured))
        {
            return Path.GetFullPath(configured);
        }

        var bundled = Path.Combine(repoRoot, "runtime", "python", "python.exe");
        if (File.Exists(bundled))
        {
            return bundled;
        }

        return "python.exe";
    }

    private static string Quote(string value) => $"\"{value.Replace("\"", "\\\"")}\"";

    private static async Task PumpAsync(StreamReader reader, string path, CancellationToken token)
    {
        await using var stream = new FileStream(path, FileMode.Append, FileAccess.Write, FileShare.ReadWrite);
        await using var writer = new StreamWriter(stream) { AutoFlush = true };
        while (!reader.EndOfStream && !token.IsCancellationRequested)
        {
            var line = await reader.ReadLineAsync(token);
            if (line is not null)
            {
                await writer.WriteLineAsync($"[{DateTimeOffset.Now:O}] {line}");
            }
        }
    }

    private static async Task IgnoreCancellation(Task task)
    {
        try { await task; }
        catch (OperationCanceledException) { }
        catch (ObjectDisposedException) { }
    }
}
