
from __future__ import print_function
from parser import parse as _parse
from itertools import combinations
from nodes import NamedTerm

class NoDocstringError(Exception):
    pass

def expand_conditionals(rule, format = True):
  def all_subsets(set_):
    list_ = list(set_)
    for size in range(0, len(list_)+1):
      for subset in combinations(list_, size):
        yield subset

  ret = []
  if isinstance(rule, basestring):
    rule = _parse(rule)

  conditionals = rule.collect_conditionals()
  for subset in all_subsets(conditionals):
    # ensure that only terms in the subset are enabled
    if format:
      ret.append(rule.select(subset).format())
    else:
      ret.append(rule.select(subset))

  return sorted(set(ret))

def create_wrapper(rule, fn):
  if isinstance(rule, basestring):
    rule = _parse(rule)

  # flattening
  rule = rule.select(())

  def wrapper(p):
    kwargs = {}
    for i, term in enumerate(rule.terms):
      if isinstance(term, NamedTerm):
        kwargs[term.name] = p[i+1]
    p[0] = fn(**kwargs)
  
  wrapper.__doc__ = rule.format()

  return wrapper

def format(rules):
  if isinstance(rules, basestring):
    rules = parse(rules)

  return '\n'.join(rule.format() for rule in rules)

def parse(defn, fname=None):
  if defn is None and fname is not None:
    raise NoDocstringError("Function %s has no docstring" % fname)
  defn = [line.strip() for line in defn.split('\n') if line.strip()]
  return [_parse(line) for line in defn]

def process_function(fn):
  rules = parse(fn.__doc__, fname=fn.__name__)
  expanded = sum((expand_conditionals(rule, format = False) for rule in rules), [])

  ret = {}
  i = 0
  for rule in expanded:
    ret['p_%s_%s' % (fn.__name__, i)] = create_wrapper(rule, fn)
    i += 1
  return ret

def process_all(globals, prefix = 'px_'):
  dict = globals.__dict__ if isinstance(globals, type) else globals
  names = [name for name in dict if name.startswith(prefix) and callable(dict[name])]
  funs = [dict[name] for name in names]
  for name in names:
    if isinstance(globals, type):
      delattr(globals, name)
    else:
      del globals[name]

  for fn in funs:
    for name, wrapper in process_function(fn).items():
      if isinstance(globals, type):
        setattr(globals, name, wrapper)
      else:
        globals[name] = wrapper
