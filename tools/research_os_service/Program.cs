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
    private Process? _process;

    public ResearchOsApiWorker(ILogger<ResearchOsApiWorker> logger)
    {
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        var repoRoot = RequirePath("RESEARCH_OS_REPO_ROOT");
        var dataDir = Environment.GetEnvironmentVariable("RESEARCH_OS_DATA_DIR")
            ?? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData), "ResearchOS");
        var pythonExe = Environment.GetEnvironmentVariable("RESEARCH_OS_PYTHON_EXE") ?? "python.exe";
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
        startInfo.Environment["RESEARCH_OS_API_HOST"] = Environment.GetEnvironmentVariable("RESEARCH_OS_API_HOST") ?? "0.0.0.0";
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
            return;
        }
        finally
        {
            await Task.WhenAll(IgnoreCancellation(stdoutTask), IgnoreCancellation(stderrTask));
        }

        if (!stoppingToken.IsCancellationRequested)
        {
            throw new InvalidOperationException($"Research OS API exited unexpectedly with code {_process.ExitCode}.");
        }
    }

    public override async Task StopAsync(CancellationToken cancellationToken)
    {
        try
        {
            if (_process is { HasExited: false })
            {
                _logger.LogInformation("Stopping Research OS API PID {Pid}", _process.Id);
                _process.Kill(entireProcessTree: true);
                await _process.WaitForExitAsync(cancellationToken);
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to stop Research OS API child process cleanly");
        }
        finally
        {
            _process?.Dispose();
            _process = null;
        }

        await base.StopAsync(cancellationToken);
    }

    private static string RequirePath(string name)
    {
        var value = Environment.GetEnvironmentVariable(name);
        if (string.IsNullOrWhiteSpace(value) || !Directory.Exists(value))
        {
            throw new InvalidOperationException($"{name} is not configured or points to a missing directory.");
        }
        return Path.GetFullPath(value);
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
    }
}
