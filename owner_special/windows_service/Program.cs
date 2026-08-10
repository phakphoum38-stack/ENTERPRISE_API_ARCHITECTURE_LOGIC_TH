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
        services.AddHostedService<OwnerFriendWorker>();
    })
    .Build();
await host.RunAsync();

sealed record ServiceOptions(string Root, string PythonExecutable, int Port, string DataDir, string ServiceName, string OwnerId)
{
    public static ServiceOptions FromArgs(string[] args)
    {
        var root = Path.GetFullPath(ReadOption(args, "--root") ?? ResolvePackagedRoot());
        var python = ReadOption(args, "--python") ?? Path.Combine(root, "runtime", "python", "python.exe");
        if (!File.Exists(python)) throw new FileNotFoundException("Bundled Python runtime not found", python);
        var portText = ReadOption(args, "--port") ?? "8790";
        if (!int.TryParse(portText, out var port) || port is < 1 or > 65535) throw new ArgumentOutOfRangeException(nameof(args), "Invalid Owner Friend port");
        var dataDir = Path.GetFullPath(ReadOption(args, "--data-dir") ?? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData), "ResearchOSOwnerSpecial"));
        var serviceName = ReadOption(args, "--service-name") ?? "ResearchOSOwnerFriendService";
        var ownerId = ReadOption(args, "--owner-id") ?? "owner";
        return new ServiceOptions(root, python, port, dataDir, serviceName, ownerId);
    }

    private static string? ReadOption(string[] args, string name)
    {
        for (var i = 0; i < args.Length; i++)
        {
            if (args[i].StartsWith(name + "=", StringComparison.OrdinalIgnoreCase)) return args[i][(name.Length + 1)..];
            if (string.Equals(args[i], name, StringComparison.OrdinalIgnoreCase) && i + 1 < args.Length) return args[i + 1];
        }
        return null;
    }

    private static string ResolvePackagedRoot()
    {
        var sibling = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, ".."));
        if (Directory.Exists(Path.Combine(sibling, "owner_special"))) return sibling;
        throw new InvalidOperationException("Owner Special packaged root could not be resolved");
    }
}

sealed class OwnerFriendWorker : BackgroundService
{
    private readonly ServiceOptions _options;
    private readonly ILogger<OwnerFriendWorker> _logger;
    private readonly SemaphoreSlim _stopLock = new(1, 1);
    private Process? _process;

    public OwnerFriendWorker(ServiceOptions options, ILogger<OwnerFriendWorker> logger)
    {
        _options = options;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        var script = Path.Combine(_options.Root, "owner_special", "scripts", "run_friend_service.py");
        if (!File.Exists(script)) throw new FileNotFoundException("Owner Friend service entrypoint not found", script);
        var serviceDir = Path.Combine(_options.DataDir, "service");
        var logsDir = Path.Combine(serviceDir, "logs");
        Directory.CreateDirectory(logsDir);
        var audit = Path.Combine(serviceDir, "audit.jsonl");
        var stdout = Path.Combine(logsDir, "service.out.log");
        var stderr = Path.Combine(logsDir, "service.err.log");

        var start = new ProcessStartInfo
        {
            FileName = _options.PythonExecutable,
            WorkingDirectory = _options.Root,
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
        };
        start.ArgumentList.Add(script);
        start.ArgumentList.Add("--owner-id"); start.ArgumentList.Add(_options.OwnerId);
        start.ArgumentList.Add("--host"); start.ArgumentList.Add("127.0.0.1");
        start.ArgumentList.Add("--port"); start.ArgumentList.Add(_options.Port.ToString());
        start.ArgumentList.Add("--data-root"); start.ArgumentList.Add(_options.DataDir);
        start.ArgumentList.Add("--audit-path"); start.ArgumentList.Add(audit);
        start.ArgumentList.Add("--repository-root"); start.ArgumentList.Add(_options.Root);
        start.Environment["PYTHONPATH"] = Path.Combine(_options.Root, "owner_special");
        start.Environment["PYTHONUNBUFFERED"] = "1";
        start.Environment["RESEARCH_OS_OWNER_DATA_ROOT"] = _options.DataDir;

        _process = new Process { StartInfo = start, EnableRaisingEvents = true };
        if (!_process.Start()) throw new InvalidOperationException("Failed to start Owner Friend process");
        _logger.LogInformation("Owner Friend service child started on 127.0.0.1:{Port} PID {Pid}", _options.Port, _process.Id);
        var stdoutTask = PumpAsync(_process.StandardOutput, stdout, stoppingToken);
        var stderrTask = PumpAsync(_process.StandardError, stderr, stoppingToken);
        try { await _process.WaitForExitAsync(stoppingToken); }
        catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested) { await StopChildAsync(CancellationToken.None); }
        finally
        {
            if (stoppingToken.IsCancellationRequested) await StopChildAsync(CancellationToken.None);
            await Task.WhenAll(IgnoreCancellation(stdoutTask), IgnoreCancellation(stderrTask));
        }
        if (!stoppingToken.IsCancellationRequested) throw new InvalidOperationException($"Owner Friend process exited unexpectedly with code {_process?.ExitCode}");
    }

    public override async Task StopAsync(CancellationToken cancellationToken)
    {
        await StopChildAsync(cancellationToken);
        await base.StopAsync(cancellationToken);
        await StopChildAsync(CancellationToken.None);
    }

    private async Task StopChildAsync(CancellationToken token)
    {
        await _stopLock.WaitAsync(token);
        try
        {
            var process = _process;
            if (process is null) return;
            try
            {
                if (!process.HasExited)
                {
                    process.Kill(entireProcessTree: true);
                    using var timeout = CancellationTokenSource.CreateLinkedTokenSource(token);
                    timeout.CancelAfter(TimeSpan.FromSeconds(10));
                    await process.WaitForExitAsync(timeout.Token);
                }
            }
            catch { try { process.Kill(entireProcessTree: true); } catch { } }
            finally { try { process.Dispose(); } catch { } _process = null; }
        }
        finally { _stopLock.Release(); }
    }

    private static async Task PumpAsync(StreamReader reader, string path, CancellationToken token)
    {
        await using var stream = new FileStream(path, FileMode.Append, FileAccess.Write, FileShare.ReadWrite);
        await using var writer = new StreamWriter(stream) { AutoFlush = true };
        while (!reader.EndOfStream && !token.IsCancellationRequested)
        {
            var line = await reader.ReadLineAsync(token);
            if (line is not null) await writer.WriteLineAsync($"[{DateTimeOffset.UtcNow:O}] {line}");
        }
    }

    private static async Task IgnoreCancellation(Task task)
    {
        try { await task; } catch (OperationCanceledException) { } catch (ObjectDisposedException) { }
    }
}
