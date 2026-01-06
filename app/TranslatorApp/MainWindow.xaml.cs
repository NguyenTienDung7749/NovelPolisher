using System.Windows;
using System.Windows.Controls;
using TranslatorApp.ViewModels;

namespace TranslatorApp
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
            
            // Handle window closing to cleanup background processes
            Closing += MainWindow_Closing;
            
            // Load saved API key if available
            if (DataContext is MainViewModel vm)
            {
                var savedKey = vm.LoadSavedApiKey();
                if (!string.IsNullOrEmpty(savedKey))
                {
                    ApiKeyBox.Password = savedKey;
                    vm.ApiKey = savedKey;
                }
            }
        }

        private void MainWindow_Closing(object? sender, System.ComponentModel.CancelEventArgs e)
        {
            // Cleanup any running backend process when window closes
            if (DataContext is MainViewModel vm && vm.IsRunning)
            {
                var result = MessageBox.Show(
                    "Đang xử lý. Bạn có chắc muốn thoát?\nTiến độ hiện tại sẽ được lưu và có thể Resume sau.",
                    "Xác nhận thoát",
                    MessageBoxButton.YesNo,
                    MessageBoxImage.Question);

                if (result == MessageBoxResult.No)
                {
                    e.Cancel = true;
                    return;
                }

                // Cancel the running process
                vm.CancelCommand.Execute(null);
            }
        }

        private void ApiKeyBox_PasswordChanged(object sender, RoutedEventArgs e)
        {
            if (DataContext is MainViewModel vm)
            {
                vm.ApiKey = ((PasswordBox)sender).Password;
            }
        }

        private void LogTextBox_TextChanged(object sender, TextChangedEventArgs e)
        {
            var textBox = (TextBox)sender;
            textBox.ScrollToEnd();
        }
        private void Minimize_Click(object sender, RoutedEventArgs e)
        {
            WindowState = WindowState.Minimized;
        }

        private void Maximize_Click(object sender, RoutedEventArgs e)
        {
            if (WindowState == WindowState.Maximized)
                WindowState = WindowState.Normal;
            else
                WindowState = WindowState.Maximized;
        }

        private void Close_Click(object sender, RoutedEventArgs e)
        {
            Close();
        }
    }
}
