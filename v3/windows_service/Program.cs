using System.Diagnostics;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

var options = ServiceOptions.FromArgs(args);

var host = Host.CreateDefaultBuilder(args)
    .UseWindowsService(service => service.ServiceName = options.ServiceName)
    .ConfigureServices(services =>
    {
        services.AddSingleton(options);
        services.AddHostedService<V3ServiceWorker>();
    })
    .Build();

await host.RunAsync();

sealed record ServiceOptions(
    string Root,
    string PythonExecutable,
    int Port,
    string DataDir,
    string ServiceName)
{
    public static ServiceOptions FromArgs(string[] args)
    {
        var root = ReadOption(args, "--root")
            ?? Environment.GetEnvironmentVariable("RESEARCH_OS_V3_ROOT")
            ?? ResolvePackagedRoot();
        root = Path.GetFullPath(root);

        var python = ReadOption(args, "--python")
            ?? Environment.GetEnvironmentVariable("RESEARCH_OS_V3_PYTHON_EXE")
            ?? ResolvePython(root);

        var portText = ReadOption(args, "--port")
            ?? Environment.GetEnvironmentVariable("RESEARCH_OS_V3_PORT")
            ?? "8788";
        if (!int.TryParse(portText, out var port) || port is < 1 or > 65535)
        {
            throw new ArgumentOutOfRangeException(nameof(args), $"Invalid V3 service port: {portText}");
        }

        var dataDir = ReadOption(args, "--data-dir")
            ?? Environment.GetEnvironmentVariable("RESEARCH_OS_V3_DATA_DIR")
            ?? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData), "ResearchOSV3");

        var serviceName = ReadOption(args, "--service-name")
            ?? Environment.GetEnvironmentVariable("RESEARCH_OS_V3_SERVICE_NAME")
            ?? "ResearchOSV3Service";

        return new ServiceOptions(root, python, port, Path.GetFullPath(dataDir), serviceName);
    }

    private static string? ReadOption(string[] args, string name)
    {
        for (var index = 0; index < args.Length; index++)
        {
            var current = args[index];
            if (current.StartsWith(name + "=", StringComparison.OrdinalIgnoreCase))
            {
                return current[(name.Length + 1)..];
            }

            if (string.Equals(current, name, StringComparison.OrdinalIgnoreCase) && index + 1 < args.Length)
            {
                return args[index + 1];
            }
        }

        return null;
    }

    private static string ResolvePackagedRoot()
    {
        var direct = Path.Combine(AppContext.BaseDirectory, "v3");
        if (Directory.Exists(Path.Combine(direct, "research_os_v3")))
        {
            return direct;
        }

        var sibling = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "v3"));
        if (Directory.Exists(Path.Combine(sibling, "research_os_v3")))
        {
            return sibling;
        }

        throw new InvalidOperationException(
            "RESEARCH_OS_V3_ROOT is not configured and a packaged V3 root could not be resolved.");
    }

    private static string ResolvePython(string root)
    {
        var bundled = Path.Combine(root, "runtime", "python", "python.exe");
        return File.Exists(bundled) ? bundled : "python.exe";
    }
}

sealed class V3ServiceWorker : BackgroundService
{
    private readonly ServiceOptions _options;
    private readonly ILogger<V3ServiceWorker> _logger;
    private readonly SemaphoreSlim _processStopLock = new(1, 1);
    private Process? _process;

    public V3ServiceWorker(ServiceOptions options, ILogger<V3ServiceWorker> logger)
    {
        _options = options;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        var scriptPath = Path.Combine(_options.Root, "scripts", "run_service.py");
        if (!File.Exists(scriptPath))
        {
            throw new FileNotFoundException("V3 local service entrypoint not found", scriptPath);
        }

        Directory.CreateDirectory(_options.DataDir);
        var logsDir = Path.Combine(_options.DataDir, "logs");
        Directory.CreateDirectory(logsDir);

        var stdoutPath = Path.Combine(logsDir, "service.out.log");
        var stderrPath = Path.Combine(logsDir, "service.err.log");

        _logger.LogInformation("Research OS V3 root: {Root}", _options.Root);
        _logger.LogInformation("Research OS V3 data: {DataDir}", _options.DataDir);
        _logger.LogInformation("Research OS V3 endpoint: http://127.0.0.1:{Port}", _options.Port);

        var startInfo = new ProcessStartInfo
        {
            FileName = _options.PythonExecutable,
            Arguments = Quote(scriptPath),
            WorkingDirectory = _options.Root,
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
        };
        startInfo.Environment["RESEARCH_OS_V3_HOST"] = "127.0.0.1";
        startInfo.Environment["RESEARCH_OS_V3_PORT"] = _options.Port.ToString();
        startInfo.Environment["RESEARCH_OS_V3_DATA_DIR"] = _options.DataDir;
        startInfo.Environment["PYTHONUNBUFFERED"] = "1";

        _process = new Process { StartInfo = startInfo, EnableRaisingEvents = true };
        if (!_process.Start())
        {
            throw new InvalidOperationException("Failed to start Research OS V3 local service process.");
        }

        _logger.LogInformation("Research OS V3 local service started with PID {Pid}", _process.Id);
        var stdoutTask = PumpAsync(_process.StandardOutput, stdoutPath, stoppingToken);
        var stderrTask = PumpAsync(_process.StandardError, stderrPath, stoppingToken);

        try
        {
            await _process.WaitForExitAsync(stoppingToken);
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
            throw new InvalidOperationException(
                $"Research OS V3 local service exited unexpectedly with code {_process?.ExitCode}.");
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
            _logger.LogWarning(ex, "Failed to terminate V3 local service during worker disposal");
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
                    _logger.LogInformation("Stopping V3 local service PID {Pid}", process.Id);
                    process.Kill(entireProcessTree: true);
                    using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
                    timeout.CancelAfter(TimeSpan.FromSeconds(10));
                    await process.WaitForExitAsync(timeout.Token);
                }
            }
            catch (OperationCanceledException)
            {
                _logger.LogWarning("Timed out stopping V3 local service PID {Pid}", SafePid(process));
                try { process.Kill(entireProcessTree: true); } catch { }
            }
            catch (InvalidOperationException)
            {
                // Process already exited between state checks.
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Failed to stop V3 local service cleanly");
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
                await writer.WriteLineAsync($"[{DateTimeOffset.UtcNow:O}] {line}");
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
