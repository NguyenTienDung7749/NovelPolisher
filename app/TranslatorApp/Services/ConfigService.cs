using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace TranslatorApp.Services
{
    /// <summary>
    /// Configuration data to persist.
    /// </summary>
    public class AppConfig
    {
        public string? EncryptedApiKey { get; set; }
        public string? ProjectId { get; set; }
        public string? Location { get; set; }
        public string? AuthFilePath { get; set; }
        public string? LastInputPath { get; set; }
        public string? LastOutputDir { get; set; }
        public string? Provider { get; set; }
        public string? Model { get; set; }
    }

    /// <summary>
    /// Service for managing application configuration with DPAPI encryption.
    /// </summary>
    public class ConfigService
    {
        private readonly string _configPath;
        private AppConfig _config;

        public ConfigService()
        {
            var appDataPath = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            var appFolder = Path.Combine(appDataPath, "NovelPolisher");
            Directory.CreateDirectory(appFolder);
            _configPath = Path.Combine(appFolder, "config.json");
            _config = Load();
        }

        private AppConfig Load()
        {
            try
            {
                if (File.Exists(_configPath))
                {
                    var json = File.ReadAllText(_configPath);
                    return JsonSerializer.Deserialize<AppConfig>(json) ?? new AppConfig();
                }
            }
            catch
            {
                // Ignore errors, return default config
            }
            return new AppConfig();
        }

        public void Save()
        {
            try
            {
                var json = JsonSerializer.Serialize(_config, new JsonSerializerOptions 
                { 
                    WriteIndented = true 
                });
                File.WriteAllText(_configPath, json);
            }
            catch
            {
                // Ignore save errors
            }
        }

        /// <summary>
        /// Encrypt and save API key using DPAPI.
        /// </summary>
        public void SaveApiKey(string apiKey)
        {
            if (string.IsNullOrEmpty(apiKey))
            {
                _config.EncryptedApiKey = null;
                Save();
                return;
            }

            try
            {
                var plainBytes = Encoding.UTF8.GetBytes(apiKey);
                var encryptedBytes = ProtectedData.Protect(
                    plainBytes, 
                    null, 
                    DataProtectionScope.CurrentUser);
                _config.EncryptedApiKey = Convert.ToBase64String(encryptedBytes);
                Save();
            }
            catch (Exception ex)
            {
                // SECURITY WARNING: DPAPI not available, storing as Base64 (NOT secure!)
                // This can happen on non-Windows platforms or restricted environments
                System.Diagnostics.Debug.WriteLine($"WARNING: DPAPI unavailable ({ex.Message}). API key stored as Base64 (NOT encrypted)!");
                _config.EncryptedApiKey = Convert.ToBase64String(Encoding.UTF8.GetBytes(apiKey));
                Save();
            }
        }

        /// <summary>
        /// Load and decrypt API key using DPAPI.
        /// </summary>
        public string? LoadApiKey()
        {
            if (string.IsNullOrEmpty(_config.EncryptedApiKey))
                return null;

            try
            {
                var encryptedBytes = Convert.FromBase64String(_config.EncryptedApiKey);
                var plainBytes = ProtectedData.Unprotect(
                    encryptedBytes, 
                    null, 
                    DataProtectionScope.CurrentUser);
                return Encoding.UTF8.GetString(plainBytes);
            }
            catch
            {
                // Try plain text fallback
                try
                {
                    return Encoding.UTF8.GetString(Convert.FromBase64String(_config.EncryptedApiKey));
                }
                catch
                {
                    return null;
                }
            }
        }

        /// <summary>
        /// Clear saved API key.
        /// </summary>
        public void ClearApiKey()
        {
            _config.EncryptedApiKey = null;
            Save();
        }

        // Property accessors for other config values
        public string? ProjectId
        {
            get => _config.ProjectId;
            set { _config.ProjectId = value; Save(); }
        }

        public string? Location
        {
            get => _config.Location ?? "us-central1";
            set { _config.Location = value; Save(); }
        }

        public string? AuthFilePath
        {
            get => _config.AuthFilePath;
            set { _config.AuthFilePath = value; Save(); }
        }

        public string? LastInputPath
        {
            get => _config.LastInputPath;
            set { _config.LastInputPath = value; Save(); }
        }

        public string? LastOutputDir
        {
            get => _config.LastOutputDir;
            set { _config.LastOutputDir = value; Save(); }
        }

        public string? Provider
        {
            get => _config.Provider ?? "studio";
            set { _config.Provider = value; Save(); }
        }

        public string? Model
        {
            get => _config.Model ?? "gemini-2.5-flash";
            set { _config.Model = value; Save(); }
        }
    }
}
