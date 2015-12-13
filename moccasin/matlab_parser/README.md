MOCCASIN MATLAB parser module
=============================

The Python module `matlab` in this directory defines a class, `MatlabGrammar`, that implements a parser for MATLAB files.  The parser is implemented using [PyParsing](http://pyparsing.wikispaces.com), a Python parsing framework.


First words and assumptions
---------------------------

MATLAB is a complex system, and the language is complex.  No parser can fully interpret MATLAB input except MATLAB.  There is no publicly-available formal definition of the MATLAB language, and MATLAB is a closed-source proprietary system; what's more, the language has evolved organically over time, which has led to a complicated mix of features that sometimes have unexpected edge cases.  Some of the syntax, such as function calls and array accesses, is ambiguous and so difficult to get right that entire papers have been written about it (for example, [Doherty, Hendren, and Radpour's 2011 paper on _kind analysis_](http://dl.acm.org/citation.cfm?doid=2076021.2048077)).

*MOCCASIN does not use MATLAB* and is designed to run without access to MATLAB or the user's MATLAB environment.  MOCCASIN's parser is designed to parse a lot of the MATLAB language, but (currently) not all of it.  The goal of MOCCASIN is to allow interpretation and translation of certain kinds of MATLAB files common in MOCCASIN's domain; for this purpose, it does not need to handle all possible MATLAB inputs.  (In fact, it already exceeds the minimum it would really need, because the authors have a tendency to overdo things....)  In keeping with this standpoint, it's worth being upfront about the following:

* The parser is more permissive than MATLAB would be.  After all, the input is assumed to be valid MATLAB in the first place, so the parser implementation can afford to be a little bit looser and thus a little bit simpler.  An implication of this is that what the parser accepts as valid is not necessarily what MATLAB would accept as valid.
* There is no support for imaginary numbers.  (In MOCCASIN's domain of application, imaginary numbers are never used.)
* There is no support for MATLAB class definitions, although MATLAB `struct` is supported.

That said, we welcome anyone who would like to improve and expand the MATLAB parser in MOCCASIN.

Readers may wonder about why MOCCASIN is not written in MATLAB or at least can assume access to the user's MATLAB environment.  Two goals of the project are (1) allow its use by people who do not have MATLAB licenses, and (2) eventually provide a MOCCASIN-based web service.  Even if MOCCASIN _were_ written in MATLAB, it could not have access to a user's MATLAB environment when MOCCASIN is embedded as a web service.  (Some implications include the inability to use any functions or toolboxes outside of what the user inputs directly to MOCCASIN.)


Basic principles of the parser
------------------------------

The main entry point are the functions `MatlabGrammar.parse_string()` and `MatlabGrammar.parse_file()`.  There are a few other public methods on the class `MatlabGrammar` for debugging and other tasks, but the basic goal of `MatlabGrammar` is to provide the two main entry points.  Both of those functions return a data structure that a caller can examine to determine what was found in a given MATLAB input string or file.

The data structure returned by the parsing functions is an object of class `MatlabContext`.  This object contains a number of fields designed for convenient processing by the rest of the MOCCASIN toolchain.  The representation of the MATLAB input itself is stored in a field called `nodes` inside the `MatlabContext` object.  This field consists of a list of `MatlabNode` objects.  They are described below.

Loosely speaking, each `MatlabNode` object represents a MATLAB statement, in the order they were read from the input file or string.  The `MatlabNode` objects are close to being an Abstract Syntax Tree (AST) representation of the input; the main difference is that the nodes capture more than only the syntax.

A difficult problem with interpreting MATLAB is that the function call forms using parentheses look identical to matrix/array accesses, and in fact, in MATLAB there's no way to tell them apart on the basis of syntax alone.  A program must determine whether the first name is a function or command, which means it's ultimately run-time dependent and depends on the functions and scripts that the user has defined.  However, as mentioned above, one of the core goals of MOCCASIN is to be able to run independently of the user's environment (and indeed, without using MATLAB at all): in other words, _MOCCASIN does not have access to the user's MATLAB environment_, so it must resort to various heuristics to try to guess whether a given entity is meant to be an array reference or a function call.  It often cannot, and then it can only return `ArrayOrFunCall` as a way to indicate it could be either one.


Hierarchy of `MatlabNode` object classes
----------------------------------------

There are numerous `MatlabNode` objects and they are hierarchically organized as depicted by the following tree diagram.

```
MatlabNode
│
├─Expression
│  ├─ Entity
│  │  ├─ Primitive
│  │  │  ├─ Number
│  │  │  ├─ String
│  │  │  ├─ Boolean
│  │  │  └─ Special       # A colon or tilde character, or the string "end".
│  │  │
│  │  ├─ Array            # Unnamed arrays ("square-bracket" type or cell).
│  │  │
│  │  ├─ Handle
│  │  │  ├─ FunHandle     # A function handle, e.g., "@foo"
│  │  │  └─ AnonFun       # An anonymous function, e.g., "@(x,y)x├y".
│  │  │
│  │  └─ Reference        # Objects that point to values.
│  │     ├─ Identifier
│  │     ├─ ArrayOrFunCall
│  │     ├─ FunCall
│  │     ├─ ArrayRef
│  │     └─ StructRef
│  │
│  └─ Operator
│     ├─ UnaryOp
│     ├─ BinaryOp
│     ├─ ColonOp
│     └─ Transpose
│
├──Definition
│  ├─ FunDef
│  ├─ Assignment
│  └─ ScopeDecl
│
├──FlowControl
│  ├─ If
│  ├─ While
│  ├─ For
│  ├─ Switch
│  ├─ TryCatch
│  └─ Branch
│
├──ShellCommand
│
└─ Comment
```

Roughly speaking, the scheme of things is as follows:

* `Expression` is the parent class of entities and operators that are the constituents of formulas.  They can appear in many places: in variable assignments, arguments of functions, value tests in `case` statements within `switch`, and so on.  Worth noting is the fact that the parser never produces `Expression` objects per se; it produces a more specific class of object such as a number or a binary operator expression.
* `Entity` objects represent things that go into `Expression` contents or other places where expressions are used.  There are a number of subclasses under `Entity`:
  * `Primitive` objects are simple literal values.
  * `Array` objects are also literal values, but are structured.  `Array` objects may be regular arrays or cell arrays.  In this parser and the Python representation, both types of arrays are treated mostly identically, with only a Boolean attribute (`is_cell`) in `Array` to distinguish them.
  * `Handle` objects in some ways are similar to `Primitive` objects and in other ways similar to `Reference`.  They have an implication of being closures, and consequently may need to be treated specially, so they are grouped into their own subclass.
  * `Reference` objects point to values.  This subclass includes simple variables as well as more complex entities, such as named arrays.  Unfortunately, they are among the most difficult objects to classify correctly in MATLAB.  The most notable case involves array accesses versus function calls, which are syntactically identical in MATLAB.  `ArrayOrFunCall` objects represent something that cannot be distinguished as either an array reference or a named function call.  This problem is discussed in a separate section below.  If the parser *can* infer that a given term is an array reference or a function call, then it will report them as `ArrayRef` or `FunCall`, respectively, but often it is impossible to tell and the parser must resort to using `ArrayOrFunCall`.
* `Operator` objects are tree-structured combinations of operators and `Entity` objects.  Operators generally have an attribute that represents the specific operation (e.g., `+` or `./`), and operands; depending on the operator, there may be one or more operands.
* `Definition` objects define `Reference` objects.
* `FlowControl` objects represent constructs with conditions and bodies.  These are the classic flow control constructs such as `if`-`then`-`else`. The bodies of these objects contain lists of statements that may contain any of the other types of objects, including other `FlowControl` type objects.
* `ShellCommand` objects represent (as you may have guessed) MATLAB shell command statements.
* `Comment` objects represent inline or block comments.


Working with MatlabNode objects
-------------------------------

Some examples will hopefully provide a better sense for how the representation works.  Suppose we have an input file containing this:

```
a = 1
```

`MatlabGrammar.parse_file()` will return a `MatlabContext` object after parsing this, and the context object will have one attribute, `nodes`, containing a list of `MatlabNode` objects.  In the present case, that list will have a length of 1 because there is only one line in the input.  Here is what the list will look like:

```
[ Assignment(lhs=Identifier(name='a'), rhs=Number(value='1')) ]
```

The `Assignment` object has two attributes, `lhs` and `rhs`, representing the left-hand and right-hand sides of the assignment, respectively.  Each of test attribute values is another `MatlabNode` object.  The object representing the variable `a` is

```
Identifier(name='a')
```

This object class has just one attribute, `name`, which can be accessed directly to get the value.  Here is an example of how you might do this by typing some commands in an interactive Python interpreter:

```
(Pdb) x = Identifier(name='a')
(Pdb) x.name
'a'
```

Here is another example.  Suppose the input file contains the following:

```
a = [1 2]
```

The parser will return the following node structure:

```
[
Assignment(lhs=Identifier(name='a'),
           rhs=Array(is_cell=False, rows=[[Number(value='1'), Number(value='2')]]))
]
```

The `Array` object has an attribute, `rows`, that stores the rows of the array contents as a list of lists.  Each list inside the outermost list represents a row.  Thus, in this simple case where there is only one row, the value of the `rows` attribute consists of a list containing one list, and this one lists contains the representations for the numbers `1` and `2` used in the array expression.

Some other types of `MatlabNode` objects have lists of nodes within them.  For instance, `While` contains an expression in the attribute `cond` and a list of nodes in the attribute `body`.  This list of nodes can contain any statement that can appear in the body of a MATLAB `while`, such as assignments, other flow-control statements, function calls, or just primitive entities or identifiers.

And those are the basics.  A caller can take the list of nodes turned by the parser and walk down the list one by one, doing whatever processing is appropriate for the caller's purposes.  Each time it encounters a `MatlabNode` object, it can extract information and process it.  The fact that everything is rooted in `MatlabNode` means that callers can use the *Visitor* pattern to implement processing algorithms.


Matrices and functions in MATLAB
--------------------------------

As mentioned above, an array access such as `foo(1, 2)` or `foo(x)` looks syntactically identical to a function call in MATLAB.  This poses a problem for the MOCCASIN parser: in many situations it can't tell if something is an array or a function, so it can't properly label the object in the parsing results.  (It is worth keeping in mind at this point that _MOCCASIN does not have access to the user's MATLAB environment_.)

The way MOCCASIN approaches this problem is the following:

1. If it can determine unambiguously that something must be an array access based on how it is used syntactically, then it will make it an object of class `ArrayRef`.  Specifically, this is the case when an array access appears on the left-hand side of an assignment statement, as well as in other situations when the access uses a bare colon character (`:`) for a subscript (because bare colons cannot be used as an argument to a function call).
2. If it can _infer_ that an object is most likely an array access, it will again make it an `ArrayRef` object.  MOCCASIN does simple type inference by remembering variables it has seen used in assignments.  When those are used in other expressions, MOCCASIN can infer they must be variable names and not function names.
3. MOCCASIN has a list of known MATLAB functions and commands.  (The list is stored in the file `functions.py` and was generated by inspecting the MATLAB documentation for the 2014b version of MATLAB.)  If an ambiguous array reference or function call has a name that appears on this list, it is inferred to be a `FunCall` and not an `ArrayRef`.
4. In all other cases, it will label the object `ArrayOrFunCall`.

Users will need to do their own processing when they encounter a `ArrayOrFunCall` object to determine what kind of thing the object really is.  In the most general case, MOCCASIN can't tell from syntax alone whether something could be a function, because without running MATLAB (and doing it _in the user's environment_, since the user's environment affects the functions and scripts that MATLAB knows about), it simply cannot know.


Expressions
-----------

MATLAB's mathematical notation is in infix format; MOCCASIN turns this into a Abstract Syntax Tree (AST) in which `Operator` objects are middle nodes and leaves are either `Entity` or other `Operator` objects (which in turn can have further child objects).  There is an `Entity` parent class for different types of primitive and other entities that have values, and there is an `Operator` parent class for operators with four classes of operators within that.

Rather than always return some sort of single container object for all expressions, the MOCCASIN parser returns the simplest representation it can produce.  What this means is that if a given MATLAB input expression (for example, the right-hand side of some variable assignment) consists of simply a number or string, then MOCCASIN will return that entity directly: it will be a `Number` or `String`.  This is true in contexts where an expression is naturally expected, as well as contexts such as function bodies where statements are expected.  (An expression appear as a statement in MATLAB simply results in MATLAB printing the evaluated value of the expression.)

Here is an example.  Suppose that an input consists of this:

```
if x > 1
    foo = true
end
```

The MOCCASIN parser will return the following (with indentation added here to improve readability):

```
[
If(cond=BinaryOp(op='>', left=Identifier(name='x'), right=Number(value='1')),
   body=[ Assignment(lhs=Identifier(name='foo'), rhs=Boolean(value='true')) ],
   elseif_tuples=[],
   else=None)
]
```

A MATLAB `if` statements's condition is an expression, and here the attribute `cond` contains the expression `BinaryOp(op='>', left=Identifier(name='x'), right=Number(value='1')`.  The body of the input consists of a single assignment statement.  MOCCASIN stores this as `body` in the `If` object instance; the value of `body` is always a list but in this case it contains only a single object, `Assignment`.  The right-hand side of the assignment is an expression consisting of a single value, which MOCCASIN represents directly as the value.

Callers can use the class hierarchy to determine what kind of objects they receive.  The Python `isinstance` operator is particular useful for this task.   For instance, for some object `thing`, the test `isinstance(thing, Primitive)` would reveal if the object is a simple value that needs no further evaluation.


Special cases
-------------

Most of what the parser returns is either an object or a list of objects.  There are two constructs that deviate from this pattern: the `elseif` terms of an `if`-`elseif` series of MATLAB statements, and the `case` parts of `switch` statements.  Both of these involve one or more pairs of condition expressions and an accompanying list of statements.  The MOCCASIN parser represents these using lists of Python tuples of the form (_condition_, _list of statements_).  The relevant attributes storing these lists of tuples on `If` and `Switch` objects are `elseif_tuples` for the former and `case_tuples` for the latter.

A different kind of special case involves `StructRef`, used to store MATLAB structure references.  In MATLAB, the fields of `struct` entities can be named statically or dynamically; the latter is known as _dynamic field references_.  Syntactically, this takes the form of a parenthesized field reference such as `somestruct.(var)`, and MATLAB evaluates the expression in the parentheses (in this case, `var`) to obtain the name of the field.  However, in MOCCASIN, a field name is represented as an `Identifier` object, the same as the name of a variable would be.  In order for callers to be able to tell whether a given structure field reference is a literal value ("the field name is `x`") or something that is to be evaluated to get the value ("the field name is stored in `x`"), MOCCASIN provides a Boolean attribute on `StructRef` called `dynamic_access`.  Its value is `True` if the `StructRef` attribute `field` is something that is meant to be evaluated.


The `MatlabContext` class and facility
--------------------------------------

When parsing MATLAB input, it is important to track the contexts in which variables and functions are discovered and used.  MOCCASIN does this with the use of a class of objects, `MatlabContext`, which also serve a dual purpose of storing some of the parse results in a form that is convenient for other parts of MOCCASIN to use.

The fields in `MatlabContext` are the following:

<dl>

<dt>name</dt> <dd>The name of this context.  If this context represents a function definition, it will be the function name; otherwise, it will be something else indicating the context.</dd>

<dt>parent</dt> <dd>The parent <code>MatlabContext</code> object of this one.</dd>

<dt>nodes</dt> <dd>The parsed representation of the MATLAB code within this context, expressed as a list of <code>MatlabNode</code> objects.  If this context is a script file, then it's the list of statements in the file; if it's a function, it's the list of statements in the function's body.</dd>

<dt>parameters</dt> <dd>If this is a function, a list of the parameters it takes.  This list contains just symbol names, not parse objects.</dd>

<dt>returns</dt> <dd>If this is a function, its return values.  This list contains just symbol names, not parse objects.</dd>

<dt>functions</dt> <dd>A dictionary of functions defined within this context.  The keys are the function names; the values are Context objects for the functions.</dd>

<dt>assignments</dt> <dd>A dictionary of the assignment statements within this context.  For simple variables (<code>a = ...</code>), the keys are the variable names.  In the case of arrays, the keys are assumed to be string representations of the array, with the following features.  If it's a bare matrix, square braces surround the matrix, semicolons separate rows, commas separate index terms within rows, and all spaces are removed.  If it's a matrix reference, it is similar but starts with a name and uses regular parentheses instead of square braces.  So, e.g., <code>[a b]</code> is turned into <code>"[a,b]"</code>, <code>"[ a ; b ; c]"</code> is turned into <code>"[a;b;c]"</code>, <code>"foo(1, 2)"</code> is turned into <code>"foo(1,2)"</code>, and so on.  The dict values are the <code>ParseResults</code> objects for the RHS.</dd>

<dt>types</dt> <dd>A dictionary of data types associated with objects.  For example, when <code>MatlabGrammar</code> encounters an assignment statement or a function definition, it stores the identifier of the assigned variable or parameter in this dictionary and sets the value to <code>"variable"</code>, to distinguish it from a <code>"function"</code>.</dd>

<dt>calls</dt> <dd>A dictionary of functions called within this context.  The keys are the function names; the values is a list of the arguments (as annotated <code>ParseResults</code> objects).</dd>

<dt>pr</dt> <dd>The <code>ParseResults</code> object related to this context.  This <code>MatlabContext</code> will contain the stuff from which we constructed this instance of a <code>MatlabContext</code> object.  The representation is awkward and not meant to be used by callers, but it's left around for debugging purposes.</dd>

<dt>file</dt> <dd>If the contents of this context came from a file, the path to the file.</dd>

</dl>

Users can access via the normal `x.propname` approach of accessing object fields in Python.

*Important: to make a copy of a `MatlabContext` object, use the Python `copy` module.  Otherwise, you will not get a deep copy of the object.


Debugging aids
--------------

The parser module directory, `matlab_parser`, contains a simple test driver in the form of the file `test.py`.  It accepts a MATLAB file as a required argument and a couple of optional arguments.  Here is an example of invoking `test.py` from inside the directory `matlab_parser` in a Linux or Mac OS X terminal:

```
./test.py matlabfile.m
```

The file `matlabfile.m` should be some (preferably very simple) MATLAB input file.  When executed, `test.py` parses the file using `MatlabGrammar.parse_string()` and prints an annotated representation of how the input was interpreted.  This representation is in the form of a `MatlabContext` object for the input file `matlabfile.m`.  If given the optional argument `-i`, then `test.py` invokes the Python `pdb` debugger after parsing the input, thus allowing you to inspect the resulting data structure interactively.  The parse results are stored in the compellingly-named variable `results`.  To begin debugging, you could print the values of the fields in the `MatlabContext` object, such as `nodes`, `types`, `assignments`, `functions`, `calls`, and others.  Other options to `test.py` can be learned by printing the help text using the option `-h`.

The `MatlabGrammar` class itself implements the printing facility in the form of the following method that callers can also use:

* `print_parse_results`: takes as a single argument the output from `MatlabGrammar.parse_string()` and prints the results.

Finally, as might be apparent from the examples above, the `MatlabNode` objects express themselves in a way that can be used to reproduce them.  That is, in contexts where Python displays the objects or you call the Python built-in function `repr` on them, they will output something that could potentially be fed back to the Python interpreter to recreate them exactly.  This can be useful to learn and explore how `MatlabNode` objects work.

