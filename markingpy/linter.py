

class LinterReport:
    """
    Report class for collecing output of the linter.
    """
    
    def __init__(self):
        self.content = []
        self.stats = None
    
    def write(self, text):
        if not text.startswith('***'):
            self.content.append(text.strip())
        
    def read(self):
        if self.content:
            return ''.join(self.content)
        else:
            return 'No issues found'
        
    def set_stats(self, stats):
        self.stats = stats


def linter(file):
    """
    Run the linter and generate a report for the submission.
    """
    from pylint.lint import PyLinter
    from pylint.reporters.text import TextReporter
    
    report = LinterReport()
    linter = PyLinter()
    linter.load_default_plugins()
    linter.read_config_file()
    linter.load_config_file()
    args = ('--disable=C0103,C0111',
            '--persistent=n',
            '--msg-template="{line}:{column:2d}: {msg_id}: {msg}"',
            )
    linter.load_command_line_configuration(args)
    linter.set_reporter(TextReporter(report))
    linter.check(file)
    report.set_stats(linter.stats)
    return report
