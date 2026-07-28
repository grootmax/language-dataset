import sys
import os

def create_sandbox_builtins():
    """
    Creates a restricted and safe set of builtins.
    """
    import builtins
    
    # White-list of safe builtins that don't allow dangerous actions like filesystem writes or sub-processes
    safe_builtins_list = [
        'abs', 'all', 'any', 'bin', 'bool', 'chr', 'dict', 'divmod', 'enumerate',
        'filter', 'float', 'format', 'frozenset', 'hash', 'hex', 'id', 'int',
        'isinstance', 'issubclass', 'iter', 'len', 'list', 'map', 'max', 'min',
        'next', 'object', 'oct', 'ord', 'pow', 'range', 'repr', 'reversed',
        'round', 'set', 'slice', 'sorted', 'str', 'sum', 'tuple', 'type', 'zip',
        'ValueError', 'TypeError', 'KeyError', 'IndexError', 'Exception', 'AssertionError',
        'super', 'property', 'classmethod', 'staticmethod', '__build_class__'
    ]
    
    safe_builtins = {}
    for name in safe_builtins_list:
        if hasattr(builtins, name):
            safe_builtins[name] = getattr(builtins, name)
            
    # Restricted __import__ that only permits safe, stateless library modules
    def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
        allowed_modules = {
            're', 'json', 'math', 'string', 'collections', 'itertools', 'copy',
            'plugins', 'plugins.base', 'core_engine' # allow base class and structures
        }
        # Check either the top-level module name or full import name
        top_name = name.split('.')[0]
        if name in allowed_modules or top_name in allowed_modules:
            return __import__(name, globals, locals, fromlist, level)
        raise ImportError(f"Import of module '{name}' is not permitted within the sandboxed environment.")
        
    safe_builtins['__import__'] = safe_import
    return safe_builtins

def exec_sandboxed(source_code, filepath="<sandbox>", extra_globals=None):
    """
    Compiles and executes python code within a sandboxed global context.
    Returns the sandboxed globals dictionary containing executed definitions.
    """
    sandbox_globals = {
        '__builtins__': create_sandbox_builtins(),
        '__name__': 'sandbox_module',
        '__file__': filepath,
    }
    
    if extra_globals:
        sandbox_globals.update(extra_globals)
        
    # Compile the source to detect syntax issues and prepare execution
    compiled = compile(source_code, filepath, 'exec')
    exec(compiled, sandbox_globals)
    
    return sandbox_globals
