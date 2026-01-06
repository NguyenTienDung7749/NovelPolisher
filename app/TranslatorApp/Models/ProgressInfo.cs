namespace TranslatorApp.Models
{
    /// <summary>
    /// Represents parsed progress information from backend stdout.
    /// </summary>
    public class ProgressInfo
    {
        public int Percent { get; set; }
        public int Chapter { get; set; }
        public string Part { get; set; } = "";

        /// <summary>
        /// Parse a PROGRESS line from backend output.
        /// Format: PROGRESS percent=NN chapter=N part=k/K
        /// </summary>
        public static ProgressInfo? Parse(string line)
        {
            if (string.IsNullOrEmpty(line) || !line.StartsWith("PROGRESS "))
                return null;

            var info = new ProgressInfo();
            var parts = line.Substring(9).Split(' ');

            foreach (var part in parts)
            {
                var keyValue = part.Split('=');
                if (keyValue.Length != 2) continue;

                switch (keyValue[0])
                {
                    case "percent":
                        if (int.TryParse(keyValue[1], out int percent))
                            info.Percent = percent;
                        break;
                    case "chapter":
                        if (int.TryParse(keyValue[1], out int chapter))
                            info.Chapter = chapter;
                        break;
                    case "part":
                        info.Part = keyValue[1];
                        break;
                }
            }

            return info;
        }
    }

    /// <summary>
    /// Represents parsed status information from backend stdout.
    /// </summary>
    public class StatusInfo
    {
        public string Stage { get; set; } = "";
        public string Input { get; set; } = "";
        public string OutDir { get; set; } = "";

        public static StatusInfo? Parse(string line)
        {
            if (string.IsNullOrEmpty(line) || !line.StartsWith("STATUS "))
                return null;

            var info = new StatusInfo();
            
            // Parse key="value" pairs
            var matches = System.Text.RegularExpressions.Regex.Matches(
                line, @"(\w+)=""([^""]*)""");

            foreach (System.Text.RegularExpressions.Match match in matches)
            {
                var key = match.Groups[1].Value;
                var value = match.Groups[2].Value;

                switch (key)
                {
                    case "stage":
                        info.Stage = value;
                        break;
                    case "input":
                        info.Input = value;
                        break;
                    case "outdir":
                        info.OutDir = value;
                        break;
                }
            }

            // Also check for stage= without quotes
            var stageMatch = System.Text.RegularExpressions.Regex.Match(line, @"stage=(\w+)");
            if (stageMatch.Success)
                info.Stage = stageMatch.Groups[1].Value;

            return info;
        }
    }

    /// <summary>
    /// Represents parsed log message from backend stdout.
    /// </summary>
    public class LogInfo
    {
        public string Message { get; set; } = "";

        public static LogInfo? Parse(string line)
        {
            if (string.IsNullOrEmpty(line) || !line.StartsWith("LOG "))
                return null;

            var info = new LogInfo();
            
            var match = System.Text.RegularExpressions.Regex.Match(
                line, @"message=""(.*)""");
            
            if (match.Success)
                info.Message = match.Groups[1].Value.Replace("\\\"", "\"");

            return info;
        }
    }

    /// <summary>
    /// Represents parsed done information from backend stdout.
    /// </summary>
    public class DoneInfo
    {
        public string OutDir { get; set; } = "";
        public string DocxPath { get; set; } = "";

        public static DoneInfo? Parse(string line)
        {
            if (string.IsNullOrEmpty(line) || !line.StartsWith("DONE "))
                return null;

            var info = new DoneInfo();
            
            var matches = System.Text.RegularExpressions.Regex.Matches(
                line, @"(\w+)=""([^""]*)""");

            foreach (System.Text.RegularExpressions.Match match in matches)
            {
                var key = match.Groups[1].Value;
                var value = match.Groups[2].Value;

                switch (key)
                {
                    case "outdir":
                        info.OutDir = value;
                        break;
                    case "docx":
                        info.DocxPath = value;
                        break;
                }
            }

            return info;
        }
    }

    /// <summary>
    /// Represents parsed error information from backend stdout.
    /// </summary>
    public class ErrorInfo
    {
        public int Code { get; set; }
        public string Message { get; set; } = "";

        public static ErrorInfo? Parse(string line)
        {
            if (string.IsNullOrEmpty(line) || !line.StartsWith("ERROR "))
                return null;

            var info = new ErrorInfo();
            
            var codeMatch = System.Text.RegularExpressions.Regex.Match(line, @"code=(\d+)");
            if (codeMatch.Success)
                info.Code = int.Parse(codeMatch.Groups[1].Value);

            var msgMatch = System.Text.RegularExpressions.Regex.Match(line, @"message=""(.*)""");
            if (msgMatch.Success)
                info.Message = msgMatch.Groups[1].Value.Replace("\\\"", "\"");

            return info;
        }
    }
}
