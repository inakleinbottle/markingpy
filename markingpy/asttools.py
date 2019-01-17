"""
Tools for manipulating Python ASTs.
"""

import ast
import astor

# noinspection PyPep8Naming
class ExerciseVisitor(ast.NodeVisitor):
    """
    Node visitor for building a new AST representing the model solutions in a
    marking scheme file.
    """

    def __init__(self):
        self.new_tree = ast.Module(body=[])

    def visit_Import(self, node):
        names = [name for name in node.names
                 if not name.name == 'markingpy']
        if names:
            self.new_tree.body.append(ast.Import(names=names))

    def visit_ImportFrom(self, node):
        if not node.module == 'markingpy':
            self.new_tree.body.append(
                ast.ImportFrom(module=node.module,
                               names=node.names,
                               level=node.level))

    def _process_attribute(self, node):
        val = node.value.id
        attr = node.attr
        if isinstance(attr, ast.Attribute):
            is_exercise = self._process_attribute(attr)
        elif isinstance(attr, ast.Name):
            is_exercise = attr.name == 'exercise'
        elif isinstance(attr, str):
            is_exercise = attr == 'exercise'
        else:
            is_exercise = False
        return is_exercise and val == 'markingpy'

    def _is_exercise(self, node):
        if not hasattr(node, 'decorator_list'):
            return False

        deco_list = node.decorator_list
        for deco in deco_list:
            print(ast.dump(deco))
            if (isinstance(deco, ast.Attribute)
                    and self._process_attribute(deco)):
                break
            elif (isinstance(deco, ast.Name)
                  and deco.id == 'exercise'):
                break
        else:
            # none of the decorators was a markingpy exercise decorator
            return False
        return True

    def visit_ClassDef(self, node):
        print(f'Visiting ClassDef {node.name}')
        if self._is_exercise(node):
            self.new_tree.body.append(ast.ClassDef(
                name=node.name,
                bases=node.bases,
                keywords=node.keywords,
                body=node.body,
                decorator_list=[]
            ))
        else:
            self.new_tree.body.append(ast.ClassDef(
                name=node.name,
                bases=node.bases,
                keywords=node.keywords,
                body=node.body,
                decorator_list=node.decorator_list
            ))

    def visit_FunctionDef(self, node):
        print(f'Visiting FunctionDef {node.name}')
        if self._is_exercise(node):
            self.new_tree.body.append(ast.FunctionDef(
                name=node.name,
                args=node.args,
                body=node.body,
                decorator_list=[],
                returns=node.returns
            ))
        else:
            self.new_tree.body.append(ast.FunctionDef(
                name=node.name,
                args=node.args,
                body=node.body,
                decorator_list=node.decorator_list,
                returns=node.returns
            ))


def get_source_for_markscheme(source):
    tree = ast.parse(source, 'marking scheme', 'exec')
    visitor = ExerciseVisitor()
    visitor.visit(tree)
    return astor.to_source(visitor.new_tree)





