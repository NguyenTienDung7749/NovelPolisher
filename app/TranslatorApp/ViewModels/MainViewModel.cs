using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Win32;
using TranslatorApp.Models;
using TranslatorApp.Services;

using System.Collections.ObjectModel;
namespace TranslatorApp.ViewModels
{
    public partial class MainViewModel : ObservableObject
    {
        private readonly ConfigService _configService;
        private Process? _backendProcess;
        private CancellationTokenSource? _cancellationTokenSource;

        public MainViewModel()
        {
            _configService = new ConfigService();
            LoadSettings();
        }

        #region Observable Properties

        [ObservableProperty]
        private string _inputPath = "";

        [ObservableProperty]
        private string _outputDir = "";

        [ObservableProperty]
        private string _apiKey = "";

        [ObservableProperty]
        private bool _rememberApiKey = true;

        [ObservableProperty]
        private string _provider = "studio";

        [ObservableProperty]
        private string _projectId = "";

        [ObservableProperty]
        private string _location = "us-central1";

        [ObservableProperty]
        private string _authFilePath = "";

        [ObservableProperty]
        private ObservableCollection<string> _availableModels = new()
        {
            "gemini-3-pro-preview",
            "gemini-3-flash-preview",
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-flash-lite-latest"
        };

        [ObservableProperty]
        private string _model = "gemini-3-pro-preview";

        [ObservableProperty]
        private string _mode = "polish_vi";

        [ObservableProperty]
        private string _exportFormat = "docx";

        [ObservableProperty]
        private int _startPage = 1;

        [ObservableProperty]
        private int _endPage = 0;

        [ObservableProperty]
        private int _maxChars = 7000;

        [ObservableProperty]
        private int _sleepMs = 250;

        [ObservableProperty]
        private string _stylePath = "";

        [ObservableProperty]
        private string _glossaryPath = "";

        [ObservableProperty]
        private int _progress = 0;

        [ObservableProperty]
        private string _statusText = "Sẵn sàng";

        [ObservableProperty]
        private string _logText = "";

        [ObservableProperty]
        private bool _isRunning = false;

        [ObservableProperty]
        private bool _hasCheckpoint = false;

        [ObservableProperty]
        private string _outputDocxPath = "";

        #endregion

        #region Computed Properties

        public bool IsStudioProvider => Provider == "studio";
        public bool IsVertexProvider => Provider == "vertex";

        partial void OnProviderChanged(string value)
        {
            OnPropertyChanged(nameof(IsStudioProvider));
            OnPropertyChanged(nameof(IsVertexProvider));
            _configService.Provider = value;
        }

        partial void OnIsRunningChanged(bool value)
        {
            // Notify all commands to re-evaluate CanExecute
            // This is critical for pause/resume buttons to enable/disable correctly
            StartCommand.NotifyCanExecuteChanged();
            ResumeCommand.NotifyCanExecuteChanged();
            CancelCommand.NotifyCanExecuteChanged();
            OpenOutputCommand.NotifyCanExecuteChanged();
        }

        partial void OnOutputDirChanged(string value)
        {
            CheckForCheckpoint();
        }

        #endregion

        #region Commands

        [RelayCommand]
        private void BrowseInput()
        {
            var dialog = new OpenFileDialog
            {
                Filter = "PDF Files (*.pdf)|*.pdf|All Files (*.*)|*.*",
                Title = "Chọn file PDF"
            };

            if (!string.IsNullOrEmpty(InputPath))
                dialog.InitialDirectory = Path.GetDirectoryName(InputPath);

            if (dialog.ShowDialog() == true)
            {
                InputPath = dialog.FileName;
                _configService.LastInputPath = InputPath;

                // Auto-set output directory
                if (string.IsNullOrEmpty(OutputDir))
                {
                    OutputDir = Path.Combine(Path.GetDirectoryName(InputPath) ?? "", "out");
                }
            }
        }

        [RelayCommand]
        private void BrowseOutput()
        {
            var dialog = new OpenFolderDialog
            {
                Title = "Chọn thư mục output"
            };

            if (!string.IsNullOrEmpty(OutputDir) && Directory.Exists(OutputDir))
                dialog.InitialDirectory = OutputDir;

            if (dialog.ShowDialog() == true)
            {
                OutputDir = dialog.FolderName;
                _configService.LastOutputDir = OutputDir;
            }
        }

        [RelayCommand]
        private void BrowseAuthFile()
        {
            var dialog = new OpenFileDialog
            {
                Filter = "JSON Files (*.json)|*.json|All Files (*.*)|*.*",
                Title = "Chọn Service Account JSON"
            };

            if (dialog.ShowDialog() == true)
            {
                AuthFilePath = dialog.FileName;
                _configService.AuthFilePath = AuthFilePath;
            }
        }

        [RelayCommand]
        private void BrowseStyle()
        {
            var dialog = new OpenFileDialog
            {
                Filter = "YAML Files (*.yaml;*.yml)|*.yaml;*.yml|All Files (*.*)|*.*",
                Title = "Chọn Style file"
            };

            if (dialog.ShowDialog() == true)
            {
                StylePath = dialog.FileName;
            }
        }

        [RelayCommand]
        private void BrowseGlossary()
        {
            var dialog = new OpenFileDialog
            {
                Filter = "JSON Files (*.json)|*.json|All Files (*.*)|*.*",
                Title = "Chọn Glossary file"
            };

            if (dialog.ShowDialog() == true)
            {
                GlossaryPath = dialog.FileName;
            }
        }

        [RelayCommand(CanExecute = nameof(CanStart))]
        private async Task StartAsync()
        {
            if (!ValidateInputs())
                return;

            // Save API key if requested
            if (RememberApiKey && !string.IsNullOrEmpty(ApiKey))
            {
                _configService.SaveApiKey(ApiKey);
            }
            else if (!RememberApiKey)
            {
                _configService.ClearApiKey();
            }

            await RunBackendAsync(overwrite: true);
        }

        private bool CanStart() => !IsRunning && !string.IsNullOrEmpty(InputPath);

        [RelayCommand(CanExecute = nameof(CanResume))]
        private async Task ResumeAsync()
        {
            if (!ValidateInputs())
                return;

            await RunBackendAsync(overwrite: false);
        }

        private bool CanResume() => !IsRunning && HasCheckpoint;

        [RelayCommand(CanExecute = nameof(CanCancel))]
        private void Cancel()
        {
            try
            {
                _cancellationTokenSource?.Cancel();
                
                if (_backendProcess != null && !_backendProcess.HasExited)
                {
                    _backendProcess.Kill(entireProcessTree: true);
                    AppendLog("⏹ Đã dừng xử lý");
                }
            }
            catch (Exception ex)
            {
                AppendLog($"⚠ Lỗi khi dừng: {ex.Message}");
            }
            finally
            {
                IsRunning = false;
                StatusText = "Đã tạm dừng - có thể Resume";
                CheckForCheckpoint();
            }
        }

        private bool CanCancel() => IsRunning;

        [RelayCommand(CanExecute = nameof(CanOpenOutput))]
        private void OpenOutput()
        {
            try
            {
                if (!string.IsNullOrEmpty(OutputDocxPath) && File.Exists(OutputDocxPath))
                {
                    Process.Start(new ProcessStartInfo
                    {
                        FileName = OutputDocxPath,
                        UseShellExecute = true
                    });
                }
                else if (!string.IsNullOrEmpty(OutputDir) && Directory.Exists(OutputDir))
                {
                    Process.Start(new ProcessStartInfo
                    {
                        FileName = OutputDir,
                        UseShellExecute = true
                    });
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Không thể mở: {ex.Message}", "Lỗi", 
                    MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private bool CanOpenOutput() => !string.IsNullOrEmpty(OutputDir) && Directory.Exists(OutputDir);

        #endregion

        #region Backend Process Management

        private async Task RunBackendAsync(bool overwrite)
        {
            IsRunning = true;
            Progress = 0;
            StatusText = "Đang khởi động...";
            LogText = "";
            _cancellationTokenSource = new CancellationTokenSource();

            try
            {
                var backendPath = FindBackendExe();
                if (string.IsNullOrEmpty(backendPath))
                {
                    throw new FileNotFoundException("Không tìm thấy backend.exe");
                }

                AppendLog($"📂 Backend: {backendPath}");
                AppendLog($"📄 Input: {InputPath}");
                AppendLog($"📁 Output: {OutputDir}");
                AppendLog("");

                var args = BuildArguments(overwrite);
                AppendLog($"🔧 Args: {args}");
                AppendLog("");

                var startInfo = new ProcessStartInfo
                {
                    FileName = backendPath,
                    Arguments = args,
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true,
                    StandardOutputEncoding = Encoding.UTF8,
                    StandardErrorEncoding = Encoding.UTF8
                };

                // Set environment variables for credentials
                if (Provider == "studio")
                {
                    startInfo.EnvironmentVariables["GEMINI_API_KEY"] = ApiKey;
                }
                else if (Provider == "vertex" && !string.IsNullOrEmpty(AuthFilePath))
                {
                    startInfo.EnvironmentVariables["GOOGLE_APPLICATION_CREDENTIALS"] = AuthFilePath;
                }

                _backendProcess = new Process { StartInfo = startInfo };

                // Use event-based async reading to avoid deadlock
                _backendProcess.OutputDataReceived += (sender, e) =>
                {
                    if (e.Data != null)
                    {
                        Application.Current.Dispatcher.InvokeAsync(() => ProcessOutputLine(e.Data));
                    }
                };

                _backendProcess.ErrorDataReceived += (sender, e) =>
                {
                    if (e.Data != null)
                    {
                        Application.Current.Dispatcher.InvokeAsync(() => ProcessOutputLine(e.Data));
                    }
                };

                _backendProcess.Start();

                // Begin async reading - this is non-blocking
                _backendProcess.BeginOutputReadLine();
                _backendProcess.BeginErrorReadLine();

                // Wait for process to exit
                await _backendProcess.WaitForExitAsync(_cancellationTokenSource.Token);

                var exitCode = _backendProcess.ExitCode;
                if (exitCode == 0)
                {
                    StatusText = "✅ Hoàn thành!";
                    AppendLog("");
                    AppendLog("🎉 Xử lý hoàn tất!");
                }
                else
                {
                    StatusText = $"❌ Lỗi (code {exitCode})";
                }
            }
            catch (OperationCanceledException)
            {
                StatusText = "⏹ Đã hủy";
            }
            catch (Exception ex)
            {
                StatusText = "❌ Lỗi";
                AppendLog($"❌ Error: {ex.Message}");
                MessageBox.Show(ex.Message, "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                IsRunning = false;
                CheckForCheckpoint();
                _backendProcess?.Dispose();
                _backendProcess = null;
            }
        }

        private void ProcessOutputLine(string line)
        {
            // Try parsing as PROGRESS
            var progressInfo = ProgressInfo.Parse(line);
            if (progressInfo != null)
            {
                Progress = progressInfo.Percent;
                StatusText = $"Chương {progressInfo.Chapter}, Phần {progressInfo.Part} ({progressInfo.Percent}%)";
                return;
            }

            // Try parsing as LOG
            var logInfo = LogInfo.Parse(line);
            if (logInfo != null)
            {
                AppendLog(logInfo.Message);
                return;
            }

            // Try parsing as STATUS
            var statusInfo = StatusInfo.Parse(line);
            if (statusInfo != null)
            {
                StatusText = $"Stage: {statusInfo.Stage}";
                return;
            }

            // Try parsing as DONE
            var doneInfo = DoneInfo.Parse(line);
            if (doneInfo != null)
            {
                OutputDocxPath = doneInfo.DocxPath;
                Progress = 100;
                StatusText = "✅ Hoàn thành!";
                AppendLog($"📄 Output: {doneInfo.DocxPath}");
                return;
            }

            // Try parsing as ERROR
            var errorInfo = ErrorInfo.Parse(line);
            if (errorInfo != null)
            {
                AppendLog($"❌ Error [{errorInfo.Code}]: {errorInfo.Message}");
                return;
            }

            // Unknown line - just log it
            if (!string.IsNullOrWhiteSpace(line))
            {
                AppendLog(line);
            }
        }

        private string BuildArguments(bool overwrite)
        {
            var sb = new StringBuilder();
            
            sb.Append($"--input \"{InputPath}\"");
            sb.Append($" --outdir \"{OutputDir}\"");
            sb.Append($" --mode {Mode}");
            sb.Append($" --provider {Provider}");
            sb.Append($" --model {Model}");
            sb.Append($" --start-page {StartPage}");
            sb.Append($" --end-page {EndPage}");
            sb.Append($" --max-chars {MaxChars}");
            sb.Append($" --sleep-ms {SleepMs}");
            sb.Append($" --export {ExportFormat}");

            // SECURITY: API key is passed via environment variable (line 345)
            // NOT via command line arguments to avoid exposure in Task Manager

            if (Provider == "vertex")
            {
                if (!string.IsNullOrEmpty(ProjectId))
                    sb.Append($" --project-id \"{ProjectId}\"");
                if (!string.IsNullOrEmpty(Location))
                    sb.Append($" --location \"{Location}\"");
                if (!string.IsNullOrEmpty(AuthFilePath))
                    sb.Append($" --auth-file \"{AuthFilePath}\"");
            }

            if (!string.IsNullOrEmpty(StylePath) && File.Exists(StylePath))
            {
                sb.Append($" --style \"{StylePath}\"");
            }

            if (!string.IsNullOrEmpty(GlossaryPath) && File.Exists(GlossaryPath))
            {
                sb.Append($" --glossary \"{GlossaryPath}\"");
            }

            if (overwrite)
            {
                sb.Append(" --overwrite");
            }

            return sb.ToString();
        }

        private string? FindBackendExe()
        {
            // Search in multiple locations
            var searchPaths = new[]
            {
                Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "backend.exe"),
                Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "dist", "backend.exe"),
                Path.Combine(Directory.GetCurrentDirectory(), "backend.exe"),
                Path.Combine(Directory.GetCurrentDirectory(), "dist", "backend.exe"),
            };

            foreach (var path in searchPaths)
            {
                if (File.Exists(path))
                    return path;
            }

            return null;
        }

        #endregion

        #region Helper Methods

        private void LoadSettings()
        {
            Provider = _configService.Provider ?? "studio";
            Model = _configService.Model ?? "gemini-3-pro-preview";
            ProjectId = _configService.ProjectId ?? "";
            Location = _configService.Location ?? "us-central1";
            AuthFilePath = _configService.AuthFilePath ?? "";

            if (!string.IsNullOrEmpty(_configService.LastInputPath))
                InputPath = _configService.LastInputPath;
            if (!string.IsNullOrEmpty(_configService.LastOutputDir))
                OutputDir = _configService.LastOutputDir;
        }

        public string? LoadSavedApiKey()
        {
            return _configService.LoadApiKey();
        }

        private bool ValidateInputs()
        {
            if (string.IsNullOrEmpty(InputPath) || !File.Exists(InputPath))
            {
                MessageBox.Show("Vui lòng chọn file PDF hợp lệ.", "Lỗi", 
                    MessageBoxButton.OK, MessageBoxImage.Warning);
                return false;
            }

            if (Provider == "studio" && string.IsNullOrEmpty(ApiKey))
            {
                MessageBox.Show("Vui lòng nhập API Key.", "Lỗi", 
                    MessageBoxButton.OK, MessageBoxImage.Warning);
                return false;
            }

            if (Provider == "vertex" && string.IsNullOrEmpty(ProjectId))
            {
                MessageBox.Show("Vui lòng nhập Project ID cho Vertex AI.", "Lỗi", 
                    MessageBoxButton.OK, MessageBoxImage.Warning);
                return false;
            }

            return true;
        }

        private void CheckForCheckpoint()
        {
            if (string.IsNullOrEmpty(OutputDir))
            {
                HasCheckpoint = false;
                return;
            }

            var checkpointPath = Path.Combine(OutputDir, "checkpoint.json");
            HasCheckpoint = File.Exists(checkpointPath);
        }

        private void AppendLog(string message)
        {
            var timestamp = DateTime.Now.ToString("HH:mm:ss");
            LogText += $"[{timestamp}] {message}\n";
        }

        #endregion
    }
}
