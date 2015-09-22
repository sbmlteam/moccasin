MOCCASIN MATLAB parser module
=============================

The Python module `matlab` in this directory defines a class, `MatlabGrammar`, that implements a parser for MATLAB files.  The parser is implemented using [PyParsing](http://pyparsing.wikispaces.com), a Python parsing framework.

First words and assumptions
---------------------------

MATLAB is a complex system, and the language is complex.  No parser can fully interpret MATLAB input except MATLAB.  MOCCASIN's parser is designed to parse a lot of the MATLAB language, but not all of it.  The goal of MOCCASIN is to allow interpretation and translation of certain kinds of MATLAB files common in MOCCASIN's domain; for this purpose, it does not need to handle all possible MATLAB inputs.  (In fact, it already exceeds the minimum it would really need, because the authors have a tendency to overdo things....)  In keeping with this standpoint, it's worth being upfront about the following:

* The parser is more permissive than MATLAB would be.  After all, the input is assumed to be valid MATLAB in the first place, so the parser implementation can afford to be a little bit looser and thus a little bit simpler.  An implication of this is that what the parser accepts as valid is not necessarily what MATLAB would accept as valid.
* There is no support for imaginary numbers.  (In MOCCASIN's domain of application, imaginary numbers are never used.)

That said, we welcome anyone who would like to improve and expand the MATLAB parser in MOCCASIN.


Basic principles of the parser
------------------------------

The main entry point are the functions `MatlabGrammar.parse_string()` and `MatlabGrammar.parse_file()`.  There are a few other public methods on the class `MatlabGrammar` for debugging and other tasks, but the basic goal of `MatlabGrammar` is to provide the two main entry points.  Both of those functions return a data structure that a caller can examine to determine what was found in a given MATLAB file.

The data structure returned by the parsing functions is an object of class `MatlabContext`.  This object contains a number of fields designed for convenient processing by the rest of the MOCCASIN toolchain.  The representation of the MATLAB input itself is stored in a field called `nodes` inside the `MatlabContext` object.  This field consists of a list of `MatlabNode` objects.

Loosely speaking, each `MatlabNode` object represents a MATLAB statement, in the order they were read from the input file or string.  The `MatlabNode` objects are close to being an Abstract Syntax Tree (AST) representation of the input; the main differences are that the nodes capture more than only the syntax (they are elaborated by some post-processing), and a true AST would put everything into a tree of nodes whereas our format is currently a mix of lists and nodes.

Hierarchy of `MatlabNode` object classes
----------------------------------------

There are numerous `MatlabNode` objects and they are hierarchically organized as depicted by the following tree diagram.

```
MatlabNode
│
├─Entity
│  ├─ Primitive
│  │  ├─ Number
│  │  ├─ String
│  │  ├─ Boolean
│  │  └─ Special     # A colon or tilde character, or the string "end".
│  │
│  ├─ Array          # Unnamed square-bracket arrays or unnamed cell arrays.
│  │
│  ├─ Handle
│  │  ├─ FunHandle   # A function handle, e.g., "@foo"
│  │  └─ AnonFun     # An anonymous function, e.g., "@(x,y)x├y".
│  │
│  ├─ Reference      # Objects that point to values.
│  │  ├─ Identifier
│  │  ├─ ArrayOrFunCall
│  │  ├─ FunCall
│  │  ├─ ArrayRef
│  │  └─ StructRef
│  │
│  └─ Operator
│     ├─ UnaryOp
│     ├─ BinaryOp
│     ├─ TernaryOp
│     └─ Transpose
│
├──Expression        # Nested list of nodes of class Entity or Expression.
│
├──Definition
│  ├─ Assignment
│  └─ FunDef
│
├──FlowControl
│  ├─ Try
│  ├─ Catch
│  ├─ Switch
│  ├─ Case
│  ├─ Otherwise
│  ├─ If
│  ├─ Elseif
│  ├─ Else
│  ├─ While
│  ├─ For
│  ├─ End
│  └─ Branch
│
├──Command
│  ├─ ShellCommand
│  └─ MatlabCommand
│
└─ Comment
```

Roughly speaking, the scheme of things is as follows:

* `Entity` objects represent things that go into `Expression` contents and may also appear in a `MatlabCommand`.  There are a number of subclasses under `Entity`:
  * `Primitive` objects are simple literal values.
  * `Array` objects are also literal values, but are structured.  `Array` objects may be regular arrays or cell arrays.  In this parser and the Python representation, they are treated mostly identically, with only a Boolean attribute (`is_cell`) in `Array` to distinguish them.
  * `Handle` objects in some ways are similar to `Primitive` objects and in other ways similar to `Reference`.  They have an implication of being closures, and consequently may need to be treated specially, so they are grouped into their own subclass.
  * `Reference` objects point to values.  This subclass includes simple variables as well as more complex entities, such as named arrays.  Unfortunately, they are among the most difficult objects to classify correctly in MATLAB.  The most notable case involves array accesses versus function calls, which are syntactically identical in MATLAB.  `ArrayOrFunCall` objects represent something that cannot be distinguished as either an array reference or a named function call.  This problem is discussed in a separate section below.  If the parser *can* infer that a given term is an array reference or a function call, then it will report them as `ArrayRef` or `FunCall`, respectively, but often it is impossible to tell.
* `Expression` objects contain `Entity` objects.  The attribute `content` in an `Expression` object contains a (possibly nested) list of `Entity` objects.
* `Definition` objects have more structure and contain other objects.
* `FlowControl` merits some additional explanation.  In the current parser, flow control statements such as while loops are treated in a very simple-minded way: they are simply objects that store the appearance of the object type, and do not contain the body of the loop or statement.  For instance, a `While` object only contains the condition.  The body of the while loop and the `End` statement will appear separately in the list of objects returned by the parser.  (This may change in the future to make the presentation properly nested.)
* `Command` objects are distinguished from other things like function calls either because they have special syntax (`ShellCommand`) or because they are not used to produce a value.  Because MATLAB syntax allows functions to be called without parentheses (that is, you can write `foo arg1 arg1` instead of `foo(arg1, arg2)`), functions called in a "command style" are sometimes returned as `MatlabCommand` rather than `FunCall`.


Working with MatlabNode objects
-------------------------------

Some examples will hopefully provide a better sense for how the representation works.  Suppose we have an input file containing this:

```
a = 1
```

`MatlabGrammar.parse_file()` will return a `MatlabContext` object after parsing this, and the context object will have one attribute, `nodes`, containing a list of `MatlabNode` objects.  In the present case, that list will have length `1` because there is only one line in the input.  Here is what the list will look like:

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

And that's basically it.  A caller can take the list of nodes turned by the parser and walk down the list one by one, doing whatever processing is appropriate for the caller's purposes.  Each time it encounters a `MatlabNode` object, it can extract information and process it.  The fact that everything is rooted in `MatlabNode` means that callers can use the *Visitor* pattern to implement processing algorithms.

A word about the syntax of expressions.  Mathematical and conditional expressions returned by the parser are in infix notation (just as in MATLAB), but binary operations are grouped left-to-right during parsing and appear as sublists.  For example, "1 + 2 + 3" will be returned as:

```
[ [ Number(value='1'), BinaryOp(op='+'), Number(value='2') ], BinaryOp(op='+'), Number(value='3') ]
```

Note the location of the nested square brackets in the output above.


Matrices and functions in MATLAB
--------------------------------

Syntactically, an array access such as `foo(1, 2)` or `foo(x)` looks identical to a function call in MATLAB.  This poses a problem for the MOCCASIN parser: in many situations it can't tell if something is an array or a function, so it can't properly label the object in the parsing results.

The way MOCCASIN approaches this problem is the following:

1. If it can determine unambiguously that something must be an array access based on how it is used syntactically, then it will make it an object of class `ArrayRef`.  Specifically, this is the case when an array access appears on the left-hand side of an assignment statement, as well as in other situations when the access uses a bare colon character (`:`) for a subscript (because bare colons cannot be used as an argument to a function call).
2. If it can _infer_ that an object is most likely an array access, it will again make it an `ArrayRef` object.  MOCCASIN does simple type inference by remembering variables it has seen used in assignments.  When those are used in other expressions, MOCCASIN can infer they must be variable names and not function names.
3. In all other cases, it will label the object `ArrayOrFunCall`.

Users will need to do their own processing when something comes back with type `ArrayOrFunCall` to determine what kind of thing the object really is.  In the most general case, MOCCASIN can't tell from syntax alone whether something could be a function, because without running MATLAB (and doing it _in the user's environment_, since the user's environment affects the functions and scripts that MATLAB knows about), it simply cannot know.


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

The parser module directory, `matlab`, contains a simple test driver in the form of the file `test.py`.  It accepts a MATLAB file as a required argument and a couple of optional arguments.  Here is an example of invoking `test.py` from inside the directory `matlab_parser` in a Linux or Mac OS X terminal:

```
./test.py matlabfile.m
```

The file `matlabfile.m` should be some (preferrably very simple) MATLAB input file.  When executed, `test.py` parses the file using `MatlabGrammar.parse_string()` and prints an annotated representation of how the input was interpreted.  This representation is in the form of a `MatlabContext` object for the input file `matlabfile.m`.  If given the optional argument `-d`, then `test.py` invokes the Python `pdb` debugger after parsing the input, thus allowing you to inspect the resulting data structure interactively.  The parse results are stored in the compellingly-named variable `results`.  To begin debugging, you could print the values of the fields in the `MatlabContext` object, such as `nodes`, `types`, `assignments`, `functions`, `calls`, and others.

The `MatlabGrammar` class itself implements the printing facility in the form of the following method that callers can also use:

* `print_parse_results`: takes as a single argument the output from `MatlabGrammar.parse_string()` and prints the results.

Finally, as might be apparent from the examples above, the `MatlabNode` objects express themselves in a way that can be used to reproduce them.  That is, in contexts where Python displays the objects or you call the Python built-in function `repr` on them, they will output something that could potentially be fed back to the Python interpreter to recreate them exactly.  This can be useful to learn and explore how `MatlabNode` objects work.

