import os



def build_style_calc(formula):
    """
    Build a style calculator by providing a formula
    """
    def calculator(stats):
        return max(0.0, eval(formula, stats))
    return calculator

DEFAULT_STYLE_FORMULA = ('10.-(float(5*error'
                            '+warning'
                            '+refactor'
                            '+convention)'
                            '/statement)*10.')



class Submission:
    
    def __init__(self, path, style_weighting=10., *,
                 style_formula=DEFAULT_STYLE_FORMULA,
                 mailto=None,
                 **kwargs):
        self.path = path
        with open(path, 'r') as f:
            self.source = f.read()
        self.reference = os.path.splitext(os.path.basename(path))[0]
        self.globals = {}
        self.feedback = {}
        self.weighting = {'style' : style_weighting}
        aggr_weight = sum(wt for wt in self.weighting.values())
        self.weighting['test'] = max((0, 100. - aggr_weight))
        self.style_calc = build_style_calc(style_formula)
        self.mailto = None
        
    @property
    def score(self):
        if not hasattr(self, '_score'):
            self._score = round(self._get_test_score() + self._get_style_score())
        return self._score
            
    def _get_style_score(self):
        if not 'style' in self.feedback:
            return 0
        else:
            style_stats = self.feedback['style'].stats
            # get score from style report
            wt = self.weighting['style']
            max_score = self.style_calc({'statement':1,
                                         'error':0,
                                         'warning':0,
                                         'convention':0,
                                         'refactor':0})
            return wt * self.style_calc(style_stats)/max_score
            
    def _get_test_score(self):
        if not 'test' in self.feedback:
            return 0
        else:
            all_tests = self.feedback['test'].all_tests
            success = [test for test in all_tests if test[0] == 'SUCCESS']
            wt = self.weighting['test']
            return wt * len(success) / len(all_tests)
      
        
    def compile(self):
        """
        Compile the submssion source code.
        """
        self.code = compile(self.source, self.path, 'exec')
        exec(self.code, self.globals)
                
    def add_feedback(self, item, feedback):
        """
        Add feedback to the submission.
        """
        self.feedback[item] = feedback
        
        
    def generate_report(self):
        """
        Generate report for this submission.
        """
        lines = []
        lines.append('Result summary for submission %s' % self.reference)
        test_report = self.feedback.get('test', None)
        style_report = self.feedback.get('style', None)
        
        if test_report is not None:
            lines.append('\nResults of test cases')
            for result, test, err in test_report.all_tests:
                lines.append('%s: %s' % (result, test_report.getDescription(test)))
        if style_report is not None:
            lines.append('\nResults of style analysis')
            lines.append(style_report.read())
            
        lines.append('\n' + '=' * 70 + '\n' + 'Final score: %s%%' % self.score)
        return '\n'.join(lines)
