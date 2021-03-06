#!/usr/bin/env python
#
# @file    functions.py
# @brief   Known MATLAB functions, for type inference purposes
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# This software is part of MOCCASIN, the Model ODE Converter for Creating
# Automated SBML INteroperability. Visit https://github.com/sbmlteam/moccasin/.
#
# Copyright (C) 2014-2018 jointly by the following organizations:
#  1. California Institute of Technology, Pasadena, CA, USA
#  2. Icahn School of Medicine at Mount Sinai, New York, NY, USA
#  3. Boston University, Boston, MA, USA
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation.  A copy of the license agreement is provided in the
# file named "COPYING.txt" included with this software distribution and also
# available online at https://github.com/sbmlteam/moccasin/.
# ------------------------------------------------------------------------- -->

# Globals.
# .............................................................................

# Certain things here are unintuitive (to me, anyway).  For example, it turns
# out that 'pi' is a function in MATLAB -- a function that takes no arguments.
# To test what kind of thing something is, you can use the MATLAB 'exist'
# function.  E.g.,:
#   exist('pi', 'builtin')
# The following page describes the meaning of the return values:
# http://www.mathworks.com/help/matlab/ref/exist.html
#
# 0 - name does not exist.
# 1 - name is a variable in the workspace.
# 2 - One of the following is true:
#     name exists on your MATLAB search path as a file with extension .m.
#     name is the name of an ordinary file on your MATLAB search path.
#     name is the full pathname to any file.
# 3 - name exists as a MEX-file on your MATLAB search path.
# 4 - name exists as a Simulink model or library file on your MATLAB search path.
# 5 - name is a built-in MATLAB function.
# 6 - name is a P-file on your MATLAB search path.
# 7 - name is a folder.
# 8 - name is a class.
#     (exist returns 0 for Java classes if you start MATLAB with the -nojvm option.)

matlab_symbols = {
    'abs': 1,
    'accumarray': 1,
    'acos': 1,
    'acosd': 1,
    'acosh': 1,
    'acot': 1,
    'acotd': 1,
    'acoth': 1,
    'acsc': 1,
    'acscd': 1,
    'acsch': 1,
    'add': 1,
    'addCause': 1,
    'addCondition': 1,
    'addConditionsFrom': 1,
    'addOptional': 1,
    'addParamValue': 1,
    'addParameter': 1,
    'addPlugin': 1,
    'addRequired': 1,
    'addTeardown': 1,
    'addcats': 1,
    'addevent': 1,
    'addframe': 1,
    'addlistener': 1,
    'addmulti': 1,
    'addpath': 1,
    'addpoints': 1,
    'addpref': 1,
    'addprop': 1,
    'addproperty': 1,
    'addsample': 1,
    'addsampletocollection': 1,
    'addtodate': 1,
    'addts': 1,
    'airy': 1,
    'align': 1,
    'alim': 1,
    'all': 1,
    'allchild': 1,
    'alpha': 1,
    'alphaShape': 1,
    'alphaSpectrum': 1,
    'alphaTriangulation': 1,
    'alphamap': 1,
    'amd': 1,
    'ancestor': 1,
    'and': 1,
    'angle': 1,
    'ans': 1,
    'any': 1,
    'append': 1,
    'applyFixture': 1,
    'area': 1,
    'array2table': 1,
    'arrayfun': 1,
    'ascii': 1,
    'asec': 1,
    'asecd': 1,
    'asech': 1,
    'asin': 1,
    'asind': 1,
    'asinh': 1,
    'assert': 1,
    'assignin': 1,
    'atan': 1,
    'atan2': 1,
    'atan2d': 1,
    'atand': 1,
    'atanh': 1,
    'audiodevinfo': 1,
    'audioinfo': 1,
    'audioplayer': 1,
    'audioread': 1,
    'audiorecorder': 1,
    'audiowrite': 1,
    'aufinfo': 1,
    'auread': 1,
    'auwrite': 1,
    'avifile': 1,
    'aviinfo': 1,
    'aviread': 1,
    'axes': 1,
    'axis': 1,
    'balance': 1,
    'bandwidth': 1,
    'bar': 1,
    'bar3': 1,
    'bar3h': 1,
    'barh': 1,
    'baryToCart': 1,
    'barycentricToCartesian': 1,
    'base2dec': 1,
    'beep': 1,
    'bench': 1,
    'besselh': 1,
    'besseli': 1,
    'besselj': 1,
    'besselk': 1,
    'bessely': 1,
    'beta': 1,
    'betainc': 1,
    'betaincinv': 1,
    'betaln': 1,
    'between': 1,
    'bicg': 1,
    'bicgstab': 1,
    'bicgstabl': 1,
    'bin2dec': 1,
    'binary': 1,
    'bitand': 1,
    'bitcmp': 1,
    'bitget': 1,
    'bitmax': 1,
    'bitnot': 1,
    'bitor': 1,
    'bitset': 1,
    'bitshift': 1,
    'bitxor': 1,
    'blanks': 1,
    'blkdiag': 1,
    'boundary': 1,
    'boundaryFacets': 1,
    'box': 1,
    'brighten': 1,
    'brush': 1,
    'bsxfun': 1,
    'builddocsearchdb': 1,
    'builtin': 1,
    'bvp4c': 1,
    'bvp5c': 1,
    'bvpget': 1,
    'bvpinit': 1,
    'bvpset': 1,
    'bvpxtend': 1,
    'caldays': 1,
    'caldiff': 1,
    'calendar': 1,
    'calendarDuration': 1,
    'callSoapService': 1,
    'calllib': 1,
    'calmonths': 1,
    'calquarters': 1,
    'calweeks': 1,
    'calyears': 1,
    'camdolly': 1,
    'cameratoolbar': 1,
    'camlight': 1,
    'camlookat': 1,
    'camorbit': 1,
    'campan': 1,
    'campos': 1,
    'camproj': 1,
    'camroll': 1,
    'camtarget': 1,
    'camup': 1,
    'camva': 1,
    'camzoom': 1,
    'cart2pol': 1,
    'cart2sph': 1,
    'cartToBary': 1,
    'cartesianToBarycentric': 1,
    'cast': 1,
    'cat': 1,
    'categorical': 1,
    'categories': 1,
    'caxis': 1,
    'cd': 1,
    'cdf2rdf': 1,
    'cdfepoch': 1,
    'cdfinfo': 1,
    'cdflib': 1,
    'cdfread': 1,
    'cdfwrite': 1,
    'ceil': 1,
    'cell': 1,
    'cell2mat': 1,
    'cell2struct': 1,
    'cell2table': 1,
    'celldisp': 1,
    'cellfun': 1,
    'cellplot': 1,
    'cellstr': 1,
    'cgs': 1,
    'char': 1,
    'checkcode': 1,
    'checkin': 1,
    'checkout': 1,
    'chol': 1,
    'cholupdate': 1,
    'circshift': 1,
    'circumcenter': 1,
    'circumcenters': 1,
    'cla': 1,
    'clabel': 1,
    'class': 1,
    'clc': 1,
    'clear': 1,
    'clearpoints': 1,
    'clearvars': 1,
    'clf': 1,
    'clipboard': 1,
    'clock': 1,
    'close': 1,
    'closereq': 1,
    'cmopts': 1,
    'cmpermute': 1,
    'cmunique': 1,
    'colamd': 1,
    'colorbar': 1,
    'colordef': 1,
    'colormap': 1,
    'colormapeditor': 1,
    'colperm': 1,
    'comet': 1,
    'comet3': 1,
    'commandhistory': 1,
    'commandwindow': 1,
    'compan': 1,
    'compass': 1,
    'complex': 1,
    'computeStrip': 1,
    'computeTile': 1,
    'computer': 1,
    'cond': 1,
    'condeig': 1,
    'condest': 1,
    'coneplot': 1,
    'conj': 1,
    'constructor': 1,
    'containers.Map': 1,
    'contour': 1,
    'contour3': 1,
    'contourc': 1,
    'contourf': 1,
    'contourslice': 1,
    'contrast': 1,
    'conv': 1,
    'conv2': 1,
    'convertDimensionsToString': 1,
    'convexHull': 1,
    'convhull': 1,
    'convhulln': 1,
    'convn': 1,
    'copy': 1,
    'copyfile': 1,
    'copyobj': 1,
    'corrcoef': 1,
    'cos': 1,
    'cosd': 1,
    'cosh': 1,
    'cot': 1,
    'cotd': 1,
    'coth': 1,
    'countcats': 1,
    'cov': 1,
    'cplxpair': 1,
    'cputime': 1,
    'createClassFromWsdl': 1,
    'createSharedTestFixture': 1,
    'createSoapMessage': 1,
    'createTestClassInstance': 1,
    'createTestMethodInstance': 1,
    'criticalAlpha': 1,
    'cross': 1,
    'csc': 1,
    'cscd': 1,
    'csch': 1,
    'csvread': 1,
    'csvwrite': 1,
    'ctranspose': 1,
    'cummax': 1,
    'cummin': 1,
    'cumprod': 1,
    'cumsum': 1,
    'cumtrapz': 1,
    'curl': 1,
    'currentDirectory': 1,
    'customverctrl': 1,
    'cylinder': 1,
    'daqread': 1,
    'daspect': 1,
    'datacursormode': 1,
    'datastore': 1,
    'datatipinfo': 1,
    'date': 1,
    'datenum': 1,
    'dateshift': 1,
    'datestr': 1,
    'datetick': 1,
    'datetime': 1,
    'datevec': 1,
    'day': 1,
    'days': 1,
    'dbclear': 1,
    'dbcont': 1,
    'dbdown': 1,
    'dblquad': 1,
    'dbmex': 1,
    'dbquit': 1,
    'dbstack': 1,
    'dbstatus': 1,
    'dbstep': 1,
    'dbstop': 1,
    'dbtype': 1,
    'dbup': 1,
    'dde23': 1,
    'ddeget': 1,
    'ddensd': 1,
    'ddesd': 1,
    'ddeset': 1,
    'deal': 1,
    'deblank': 1,
    'dec2base': 1,
    'dec2bin': 1,
    'dec2hex': 1,
    'decic': 1,
    'deconv': 1,
    'del2': 1,
    'delaunay': 1,
    'delaunayTriangulation': 1,
    'delaunayn': 1,
    'delete': 1,
    'deleteproperty': 1,
    'delevent': 1,
    'delsample': 1,
    'delsamplefromcollection': 1,
    'demo': 1,
    'depdir': 1,
    'depfun': 1,
    'det': 1,
    'details': 1,
    'detrend': 1,
    'deval': 1,
    'diag': 1,
    'diagnose': 1,
    'dialog': 1,
    'diary': 1,
    'diff': 1,
    'diffuse': 1,
    'dir': 1,
    'disp': 1,
    'display': 1,
    'displayEmptyObject': 1,
    'displayNonScalarObject': 1,
    'displayPropertyGroups': 1,
    'displayScalarHandleToDeletedObject': 1,
    'displayScalarObject': 1,
    'dither': 1,
    'divergence': 1,
    'dlmread': 1,
    'dlmwrite': 1,
    'dmperm': 1,
    'doc': 1,
    'docsearch': 1,
    'dos': 1,
    'dot': 1,
    'double': 1,
    'dragrect': 1,
    'drawnow': 1,
    'dsearchn': 1,
    'duration': 1,
    'dynamicprops': 1,
    'echo': 1,
    'echodemo': 1,
    'edgeAttachments': 1,
    'edges': 1,
    'edit': 1,
    'eig': 1,
    'eigs': 1,
    'ellipj': 1,
    'ellipke': 1,
    'ellipsoid': 1,
    'empty': 1,
    'enableNETfromNetworkDrive': 1,
    'enableservice': 1,
    'enumeration': 1,
    'eomday': 1,
    'eps': 1,
    'eq': 1,
    'erf': 1,
    'erfc': 1,
    'erfcinv': 1,
    'erfcx': 1,
    'erfinv': 1,
    'error': 1,
    'errorbar': 1,
    'errordlg': 1,
    'etime': 1,
    'etree': 1,
    'etreeplot': 1,
    'eval': 1,
    'evalc': 1,
    'evalin': 1,
    'eventlisteners': 1,
    'events': 1,
    'exceltime': 1,
    'exifread': 1,
    'exist': 1,
    'exit': 1,
    'exp': 1,
    'expint': 1,
    'expm': 1,
    'expm1': 1,
    'export2wsdlg': 1,
    'eye': 1,
    'ezcontour': 1,
    'ezcontourf': 1,
    'ezmesh': 1,
    'ezmeshc': 1,
    'ezplot': 1,
    'ezplot3': 1,
    'ezpolar': 1,
    'ezsurf': 1,
    'ezsurfc': 1,
    'faceNormal': 1,
    'faceNormals': 1,
    'factor': 1,
    'factorial': 1,
    'false': 1,
    'fclose': 1,
    'feather': 1,
    'featureEdges': 1,
    'feof': 1,
    'ferror': 1,
    'feval': 1,
    'fewerbins': 1,
    'fft': 1,
    'fft2': 1,
    'fftn': 1,
    'fftshift': 1,
    'fftw': 1,
    'fgetl': 1,
    'fgets': 1,
    'fieldnames': 1,
    'figure': 1,
    'figurepalette': 1,
    'fileattrib': 1,
    'filebrowser': 1,
    'filemarker': 1,
    'fileparts': 1,
    'fileread': 1,
    'filesep': 1,
    'fill': 1,
    'fill3': 1,
    'filter': 1,
    'filter2': 1,
    'find': 1,
    'findall': 1,
    'findfigs': 1,
    'findobj': 1,
    'findprop': 1,
    'findstr': 1,
    'finish': 1,
    'fitsdisp': 1,
    'fitsinfo': 1,
    'fitsread': 1,
    'fitswrite': 1,
    'fix': 1,
    'flintmax': 1,
    'flip': 1,
    'flipdim': 1,
    'fliplr': 1,
    'flipud': 1,
    'floor': 1,
    'flow': 1,
    'fminbnd': 1,
    'fminsearch': 1,
    'fopen': 1,
    'forInteractiveUse': 1,
    'format': 1,
    'fplot': 1,
    'fprintf': 1,
    'frame2im': 1,
    'fread': 1,
    'freeBoundary': 1,
    'freqspace': 1,
    'frewind': 1,
    'fromClass': 1,
    'fromFile': 1,
    'fromFolder': 1,
    'fromMethod': 1,
    'fromName': 1,
    'fromPackage': 1,
    'fscanf': 1,
    'fseek': 1,
    'ftell': 1,
    'full': 1,
    'fullfile': 1,
    'func2str': 1,
    'function_handle': 1,
    'functions': 1,
    'functiontests': 1,
    'funm': 1,
    'fwrite': 1,
    'fzero': 1,
    'gallery': 1,
    'gamma': 1,
    'gammainc': 1,
    'gammaincinv': 1,
    'gammaln': 1,
    'gca': 1,
    'gcbf': 1,
    'gcbo': 1,
    'gcd': 1,
    'gcf': 1,
    'gcmr': 1,
    'gco': 1,
    'ge': 1,
    'genpath': 1,
    'genvarname': 1,
    'get': 1,
    'getClassNameForHeader': 1,
    'getDefaultScalarElement': 1,
    'getDeletedHandleText': 1,
    'getDetailedFooter': 1,
    'getDetailedHeader': 1,
    'getDiagnosticFor': 1,
    'getDisplayableString': 1,
    'getFileFormats': 1,
    'getFooter': 1,
    'getHandleText': 1,
    'getHeader': 1,
    'getNegativeDiagnosticFor': 1,
    'getPostActValString': 1,
    'getPostConditionString': 1,
    'getPostDescriptionString': 1,
    'getPostExpValString': 1,
    'getPreDescriptionString': 1,
    'getProfiles': 1,
    'getPropertyGroups': 1,
    'getReport': 1,
    'getSharedTestFixtures': 1,
    'getSimpleHeader': 1,
    'getTag': 1,
    'getTagNames': 1,
    'getVersion': 1,
    'getabstime': 1,
    'getappdata': 1,
    'getaudiodata': 1,
    'getdatasamples': 1,
    'getdatasamplesize': 1,
    'getdisp': 1,
    'getenv': 1,
    'getfield': 1,
    'getframe': 1,
    'getinterpmethod': 1,
    'getnext': 1,
    'getpixelposition': 1,
    'getpoints': 1,
    'getpref': 1,
    'getqualitydesc': 1,
    'getsamples': 1,
    'getsampleusingtime': 1,
    'gettimeseriesnames': 1,
    'gettsafteratevent': 1,
    'gettsafterevent': 1,
    'gettsatevent': 1,
    'gettsbeforeatevent': 1,
    'gettsbeforeevent': 1,
    'gettsbetweenevents': 1,
    'ginput': 1,
    'global': 1,
    'gmres': 1,
    'gobjects': 1,
    'gplot': 1,
    'grabcode': 1,
    'gradient': 1,
    'graymon': 1,
    'grid': 1,
    'griddata': 1,
    'griddatan': 1,
    'griddedInterpolant': 1,
    'groot': 1,
    'gsvd': 1,
    'gt': 1,
    'gtext': 1,
    'guidata': 1,
    'guide': 1,
    'guihandles': 1,
    'gunzip': 1,
    'gzip': 1,
    'h5create': 1,
    'h5disp': 1,
    'h5info': 1,
    'h5read': 1,
    'h5readatt': 1,
    'h5write': 1,
    'h5writeatt': 1,
    'hadamard': 1,
    'handle': 1,
    'hankel': 1,
    'hasFrame': 1,
    'hasdata': 1,
    'hasnext': 1,
    'hdf5info': 1,
    'hdf5read': 1,
    'hdf5write': 1,
    'hdfan': 1,
    'hdfdf24': 1,
    'hdfdfr8': 1,
    'hdfh': 1,
    'hdfhd': 1,
    'hdfhe': 1,
    'hdfhx': 1,
    'hdfinfo': 1,
    'hdfml': 1,
    'hdfpt': 1,
    'hdfread': 1,
    'hdftool': 1,
    'hdfv': 1,
    'hdfvf': 1,
    'hdfvh': 1,
    'hdfvs': 1,
    'height': 1,
    'help': 1,
    'helpbrowser': 1,
    'helpdesk': 1,
    'helpdlg': 1,
    'helpwin': 1,
    'hess': 1,
    'hex2dec': 1,
    'hex2num': 1,
    'hgexport': 1,
    'hggroup': 1,
    'hgload': 1,
    'hgsave': 1,
    'hgsetget': 1,
    'hgtransform': 1,
    'hidden': 1,
    'hilb': 1,
    'hist': 1,
    'histc': 1,
    'histcounts': 1,
    'histogram': 1,
    'hms': 1,
    'hold': 1,
    'home': 1,
    'horzcat': 1,
    'hour': 1,
    'hours': 1,
    'hsv2rgb': 1,
    'hypot': 1,
    'ichol': 1,
    'idealfilter': 1,
    'idivide': 1,
    'ifft': 1,
    'ifft2': 1,
    'ifftn': 1,
    'ifftshift': 1,
    'ilu': 1,
    'im2double': 1,
    'im2frame': 1,
    'im2java': 1,
    'imag': 1,
    'image': 1,
    'imagesc': 1,
    'imapprox': 1,
    'imfinfo': 1,
    'imformats': 1,
    'import': 1,
    'importdata': 1,
    'imread': 1,
    'imshow': 1,
    'imwrite': 1,
    'inOutStatus': 1,
    'inShape': 1,
    'incenter': 1,
    'incenters': 1,
    'ind2rgb': 1,
    'ind2sub': 1,
    'inferiorto': 1,
    'info': 1,
    'inline': 1,
    'inmem': 1,
    'innerjoin': 1,
    'inpolygon': 1,
    'input': 1,
    'inputParser': 1,
    'inputdlg': 1,
    'inputname': 1,
    'inspect': 1,
    'instrcallback': 1,
    'instrfind': 1,
    'instrfindall': 1,
    'int16': 1,
    'int2str': 1,
    'int32': 1,
    'int64': 1,
    'int8': 1,
    'integral': 1,
    'integral2': 1,
    'integral3': 1,
    'interfaces': 1,
    'interp1': 1,
    'interp1q': 1,
    'interp2': 1,
    'interp3': 1,
    'interpft': 1,
    'interpn': 1,
    'interpstreamspeed': 1,
    'intersect': 1,
    'intmax': 1,
    'intmin': 1,
    'inv': 1,
    'invhilb': 1,
    'invoke': 1,
    'ipermute': 1,
    'iqr': 1,
    'isCompatibile': 1,
    'isConnected': 1,
    'isEdge': 1,
    'isInterior': 1,
    'isKey': 1,
    'isNull': 1,
    'isTiled': 1,
    'isa': 1,
    'isappdata': 1,
    'isbanded': 1,
    'isbetween': 1,
    'iscalendarduration': 1,
    'iscategorical': 1,
    'iscategory': 1,
    'iscell': 1,
    'iscellstr': 1,
    'ischar': 1,
    'iscolumn': 1,
    'iscom': 1,
    'isdatetime': 1,
    'isdiag': 1,
    'isdir': 1,
    'isdst': 1,
    'isduration': 1,
    'isempty': 1,
    'isequal': 1,
    'isequaln': 1,
    'isequalwithequalnans': 1,
    'isevent': 1,
    'isfield': 1,
    'isfinite': 1,
    'isfloat': 1,
    'isglobal': 1,
    'isgraphics': 1,
    'ishandle': 1,
    'ishermitian': 1,
    'ishghandle': 1,
    'ishold': 1,
    'isinf': 1,
    'isinteger': 1,
    'isinterface': 1,
    'isjava': 1,
    'iskeyword': 1,
    'isletter': 1,
    'islogical': 1,
    'ismac': 1,
    'ismatrix': 1,
    'ismember': 1,
    'ismethod': 1,
    'ismissing': 1,
    'isnan': 1,
    'isnat': 1,
    'isnumeric': 1,
    'isobject': 1,
    'isocaps': 1,
    'isocolors': 1,
    'isonormals': 1,
    'isordinal': 1,
    'isosurface': 1,
    'ispc': 1,
    'ispref': 1,
    'isprime': 1,
    'isprop': 1,
    'isprotected': 1,
    'isreal': 1,
    'isrow': 1,
    'isscalar': 1,
    'issorted': 1,
    'isspace': 1,
    'issparse': 1,
    'isstr': 1,
    'isstrprop': 1,
    'isstruct': 1,
    'isstudent': 1,
    'issymmetric': 1,
    'istable': 1,
    'istril': 1,
    'istriu': 1,
    'isundefined': 1,
    'isunix': 1,
    'isvalid': 1,
    'isvarname': 1,
    'isvector': 1,
    'isweekend': 1,
    'javaArray': 1,
    'javaMethod': 1,
    'javaMethodEDT': 1,
    'javaObject': 1,
    'javaObjectEDT': 1,
    'javaaddpath': 1,
    'javachk': 1,
    'javaclasspath': 1,
    'javarmpath': 1,
    'join': 1,
    'juliandate': 1,
    'keyboard': 1,
    'keys': 1,
    'kron': 1,
    'last': 1,
    'lastDirectory': 1,
    'lasterr': 1,
    'lasterror': 1,
    'lastwarn': 1,
    'lcm': 1,
    'ldivide': 1,
    'ldl': 1,
    'le': 1,
    'legend': 1,
    'legendre': 1,
    'length': 1,
    'lib.pointer': 1,
    'libfunctions': 1,
    'libfunctionsview': 1,
    'libisloaded': 1,
    'libpointer': 1,
    'libstruct': 1,
    'license': 1,
    'light': 1,
    'lightangle': 1,
    'lighting': 1,
    'lin2mu': 1,
    'line': 1,
    'linkaxes': 1,
    'linkdata': 1,
    'linkprop': 1,
    'linsolve': 1,
    'linspace': 1,
    'listdlg': 1,
    'listfonts': 1,
    'load': 1,
    'loadlibrary': 1,
    'loadobj': 1,
    'localfunctions': 1,
    'log': 1,
    'log10': 1,
    'log1p': 1,
    'log2': 1,
    'logical': 1,
    'loglog': 1,
    'logm': 1,
    'logspace': 1,
    'lookfor': 1,
    'lower': 1,
    'ls': 1,
    'lscov': 1,
    'lsqnonneg': 1,
    'lsqr': 1,
    'lt': 1,
    'lu': 1,
    'magic': 1,
    'makehgtform': 1,
    'mapreduce': 1,
    'mapreducer': 1,
    'mat2cell': 1,
    'mat2str': 1,
    'material': 1,
    'matfile': 1,
    'matlab': 1,
    'matlabrc': 1,
    'matlabroot': 1,
    'max': 1,
    'maxNumCompThreads': 1,
    'mean': 1,
    'median': 1,
    'memmapfile': 1,
    'memory': 1,
    'menu': 1,
    'mergecats': 1,
    'mesh': 1,
    'meshc': 1,
    'meshgrid': 1,
    'meshz': 1,
    'metaclass': 1,
    'methods': 1,
    'methodsview': 1,
    'mex': 1,
    'mexext': 1,
    'mfilename': 1,
    'mget': 1,
    'min': 1,
    'minres': 1,
    'minus': 1,
    'minute': 1,
    'minutes': 1,
    'mislocked': 1,
    'mkdir': 1,
    'mkpp': 1,
    'mldivide': 1,
    'mlint': 1,
    'mlintrpt': 1,
    'mlock': 1,
    'mmfileinfo': 1,
    'mmreader': 1,
    'mod': 1,
    'mode': 1,
    'month': 1,
    'more': 1,
    'morebins': 1,
    'move': 1,
    'movefile': 1,
    'movegui': 1,
    'movie': 1,
    'movie2avi': 1,
    'mpower': 1,
    'mput': 1,
    'mrdivide': 1,
    'msgbox': 1,
    'mtimes': 1,
    'mu2lin': 1,
    'multibandread': 1,
    'multibandwrite': 1,
    'munlock': 1,
    'namelengthmax': 1,
    'nargchk': 1,
    'nargin': 1,
    'narginchk': 1,
    'nargout': 1,
    'nargoutchk': 1,
    'native2unicode': 1,
    'nccreate': 1,
    'ncdisp': 1,
    'nchoosek': 1,
    'ncinfo': 1,
    'ncread': 1,
    'ncreadatt': 1,
    'ncwrite': 1,
    'ncwriteatt': 1,
    'ncwriteschema': 1,
    'ndgrid': 1,
    'ndims': 1,
    'ne': 1,
    'nearestNeighbor': 1,
    'neighbors': 1,
    'newplot': 1,
    'nextDirectory': 1,
    'nextpow2': 1,
    'nnz': 1,
    'noanimate': 1,
    'nonzeros': 1,
    'norm': 1,
    'normest': 1,
    'not': 1,
    'notebook': 1,
    'notify': 1,
    'now': 1,
    'nthroot': 1,
    'null': 1,
    'num2cell': 1,
    'num2hex': 1,
    'num2str': 1,
    'numRegions': 1,
    'numberOfStrips': 1,
    'numberOfTiles': 1,
    'numel': 1,
    'nzmax': 1,
    'ode113': 1,
    'ode15i': 1,
    'ode15s': 1,
    'ode23': 1,
    'ode23s': 1,
    'ode23t': 1,
    'ode23tb': 1,
    'ode45': 1,
    'odeget': 1,
    'odeset': 1,
    'odextend': 1,
    'onCleanup': 1,
    'ones': 1,
    'open': 1,
    'openfig': 1,
    'opengl': 1,
    'openvar': 1,
    'optimget': 1,
    'optimset': 1,
    'or': 1,
    'ordeig': 1,
    'orderfields': 1,
    'ordqz': 1,
    'ordschur': 1,
    'orient': 1,
    'orth': 1,
    'outerjoin': 1,
    'pack': 1,
    'padecoef': 1,
    'pagesetupdlg': 1,
    'pan': 1,
    'pareto': 1,
    'parfor': 1,
    'parse': 1,
    'parseSoapResponse': 1,
    'pascal': 1,
    'patch': 1,
    'path': 1,
    'path2rc': 1,
    'pathsep': 1,
    'pathtool': 1,
    'pause': 1,
    'pbaspect': 1,
    'pcg': 1,
    'pchip': 1,
    'pcode': 1,
    'pcolor': 1,
    'pdepe': 1,
    'pdeval': 1,
    'peaks': 1,
    'perimeter': 1,
    'perl': 1,
    'perms': 1,
    'permute': 1,
    'persistent': 1,
    'pi': 1,
    'pie': 1,
    'pie3': 1,
    'pinv': 1,
    'planerot': 1,
    'play': 1,
    'playblocking': 1,
    'plot': 1,
    'plot3': 1,
    'plotbrowser': 1,
    'plotedit': 1,
    'plotmatrix': 1,
    'plottools': 1,
    'plotyy': 1,
    'plus': 1,
    'plus': 1,
    'pointLocation': 1,
    'pol2cart': 1,
    'polar': 1,
    'poly': 1,
    'polyarea': 1,
    'polyder': 1,
    'polyeig': 1,
    'polyfit': 1,
    'polyint': 1,
    'polyval': 1,
    'polyvalm': 1,
    'posixtime': 1,
    'pow2': 1,
    'power': 1,
    'ppval': 1,
    'prefdir': 1,
    'preferences': 1,
    'preview': 1,
    'primes': 1,
    'print': 1,
    'printdlg': 1,
    'printopt': 1,
    'printpreview': 1,
    'prod': 1,
    'profile': 1,
    'profsave': 1,
    'propedit': 1,
    'properties': 1,
    'propertyeditor': 1,
    'psi': 1,
    'publish': 1,
    'pwd': 1,
    'pyargs': 1,
    'pyversion': 1,
    'qmr': 1,
    'qr': 1,
    'qrdelete': 1,
    'qrinsert': 1,
    'qrupdate': 1,
    'quad': 1,
    'quad2d': 1,
    'quadgk': 1,
    'quadl': 1,
    'quadv': 1,
    'quarter': 1,
    'questdlg': 1,
    'quit': 1,
    'quiver': 1,
    'quiver3': 1,
    'qz': 1,
    'rand': 1,
    'randi': 1,
    'randn': 1,
    'randperm': 1,
    'rank': 1,
    'rat': 1,
    'rats': 1,
    'rbbox': 1,
    'rcond': 1,
    'rdivide': 1,
    'read': 1,
    'readEncodedStrip': 1,
    'readEncodedTile': 1,
    'readFrame': 1,
    'readRGBAImage': 1,
    'readRGBAStrip': 1,
    'readRGBATile': 1,
    'readall': 1,
    'readasync': 1,
    'readtable': 1,
    'real': 1,
    'reallog': 1,
    'realmax': 1,
    'realmin': 1,
    'realpow': 1,
    'realsqrt': 1,
    'record': 1,
    'recordblocking': 1,
    'rectangle': 1,
    'rectint': 1,
    'recycle': 1,
    'reducepatch': 1,
    'reducevolume': 1,
    'refresh': 1,
    'refreshdata': 1,
    'regexp': 1,
    'regexpi': 1,
    'regexprep': 1,
    'regexptranslate': 1,
    'registerevent': 1,
    'rehash': 1,
    'release': 1,
    'rem': 1,
    'remove': 1,
    'removecats': 1,
    'removets': 1,
    'rename': 1,
    'renamecats': 1,
    'reordercats': 1,
    'repmat': 1,
    'resample': 1,
    'reset': 1,
    'reshape': 1,
    'residue': 1,
    'restoredefaultpath': 1,
    'rethrow': 1,
    'rewriteDirectory': 1,
    'rgb2gray': 1,
    'rgb2hsv': 1,
    'rgb2ind': 1,
    'rgbplot': 1,
    'ribbon': 1,
    'rmappdata': 1,
    'rmdir': 1,
    'rmfield': 1,
    'rmpath': 1,
    'rmpref': 1,
    'rng': 1,
    'roots': 1,
    'rose': 1,
    'rosser': 1,
    'rot90': 1,
    'rotate': 1,
    'rotate3d': 1,
    'round': 1,
    'rowfun': 1,
    'rref': 1,
    'rsf2csf': 1,
    'run': 1,
    'runTest': 1,
    'runTestClass': 1,
    'runTestMethod': 1,
    'runTestSuite': 1,
    'runtests': 1,
    'satisfiedBy': 1,
    'save': 1,
    'saveas': 1,
    'savefig': 1,
    'saveobj': 1,
    'savepath': 1,
    'scatter': 1,
    'scatter3': 1,
    'scatteredInterpolant': 1,
    'schur': 1,
    'script': 1,
    'sec': 1,
    'secd': 1,
    'sech': 1,
    'second': 1,
    'seconds': 1,
    'selectIf': 1,
    'selectmoveresize': 1,
    'semilogx': 1,
    'semilogy': 1,
    'sendmail': 1,
    'serial': 1,
    'serialbreak': 1,
    'set': 1,
    'setDirectory': 1,
    'setSubDirectory': 1,
    'setTag': 1,
    'setabstime': 1,
    'setappdata': 1,
    'setcats': 1,
    'setdatatype': 1,
    'setdiff': 1,
    'setdisp': 1,
    'setenv': 1,
    'setfield': 1,
    'setinterpmethod': 1,
    'setpixelposition': 1,
    'setpref': 1,
    'setstr': 1,
    'settimeseriesnames': 1,
    'setuniformtime': 1,
    'setup': 1,
    'setupSharedTestFixture': 1,
    'setupTestClass': 1,
    'setupTestMethod': 1,
    'setxor': 1,
    'shading': 1,
    'shg': 1,
    'shiftdim': 1,
    'showplottool': 1,
    'shrinkfaces': 1,
    'sign': 1,
    'sin': 1,
    'sind': 1,
    'single': 1,
    'sinh': 1,
    'size': 1,
    'slice': 1,
    'smooth3': 1,
    'snapnow': 1,
    'sort': 1,
    'sortrows': 1,
    'sound': 1,
    'soundsc': 1,
    'spalloc': 1,
    'sparse': 1,
    'spaugment': 1,
    'spconvert': 1,
    'spdiags': 1,
    'specular': 1,
    'speye': 1,
    'spfun': 1,
    'sph2cart': 1,
    'sphere': 1,
    'spinmap': 1,
    'spline': 1,
    'split': 1,
    'spones': 1,
    'spparms': 1,
    'sprand': 1,
    'sprandn': 1,
    'sprandsym': 1,
    'sprank': 1,
    'sprintf': 1,
    'spy': 1,
    'sqrt': 1,
    'sqrtm': 1,
    'squeeze': 1,
    'ss2tf': 1,
    'sscanf': 1,
    'stack': 1,
    'stairs': 1,
    'standardizeMissing': 1,
    'start': 1,
    'startat': 1,
    'startup': 1,
    'std': 1,
    'stem': 1,
    'stem3': 1,
    'stop': 1,
    'stopasync': 1,
    'str2double': 1,
    'str2func': 1,
    'str2mat': 1,
    'str2num': 1,
    'strcat': 1,
    'strcmp': 1,
    'strcmpi': 1,
    'stream2': 1,
    'stream3': 1,
    'streamline': 1,
    'streamparticles': 1,
    'streamribbon': 1,
    'streamslice': 1,
    'streamtube': 1,
    'strfind': 1,
    'strings': 1,
    'strjoin': 1,
    'strjust': 1,
    'strmatch': 1,
    'strncmp': 1,
    'strncmpi': 1,
    'strread': 1,
    'strrep': 1,
    'strsplit': 1,
    'strtok': 1,
    'strtrim': 1,
    'struct': 1,
    'struct2cell': 1,
    'struct2table': 1,
    'structfun': 1,
    'strvcat': 1,
    'sub2ind': 1,
    'subplot': 1,
    'subsasgn': 1,
    'subsindex': 1,
    'subspace': 1,
    'subsref': 1,
    'substruct': 1,
    'subvolume': 1,
    'sum': 1,
    'summary': 1,
    'superclasses': 1,
    'superiorto': 1,
    'support': 1,
    'supportPackageInstaller': 1,
    'supports': 1,
    'surf': 1,
    'surf2patch': 1,
    'surface': 1,
    'surfaceArea': 1,
    'surfc': 1,
    'surfl': 1,
    'surfnorm': 1,
    'svd': 1,
    'svds': 1,
    'swapbytes': 1,
    'sylvester': 1,
    'symamd': 1,
    'symbfact': 1,
    'symmlq': 1,
    'symrcm': 1,
    'symvar': 1,
    'synchronize': 1,
    'syntax': 1,
    'system': 1,
    'table': 1,
    'table2array': 1,
    'table2cell': 1,
    'table2struct': 1,
    'tan': 1,
    'tand': 1,
    'tanh': 1,
    'tar': 1,
    'targetupdater': 1,
    'tcpclient': 1,
    'teardown': 1,
    'teardownSharedTestFixture': 1,
    'teardownTestClass': 1,
    'teardownTestMethod': 1,
    'tempdir': 1,
    'tempname': 1,
    'tetramesh': 1,
    'texlabel': 1,
    'text': 1,
    'textread': 1,
    'textscan': 1,
    'textwrap': 1,
    'tfqmr': 1,
    'throw': 1,
    'throwAsCaller': 1,
    'tic': 1,
    'time': 1,
    'timeit': 1,
    'timeofday': 1,
    'timer': 1,
    'timerfind': 1,
    'timerfindall': 1,
    'times': 1,
    'timeseries': 1,
    'title': 1,
    'toc': 1,
    'todatenum': 1,
    'toeplitz': 1,
    'toolboxdir': 1,
    'trace': 1,
    'transpose': 1,
    'transpose': 1,
    'trapz': 1,
    'treelayout': 1,
    'treeplot': 1,
    'triangulation': 1,
    'tril': 1,
    'trimesh': 1,
    'triplequad': 1,
    'triplot': 1,
    'trisurf': 1,
    'triu': 1,
    'true': 1,
    'tscollection': 1,
    'tsdata.event': 1,
    'tsearchn': 1,
    'type': 1,
    'typecast': 1,
    'tzoffset': 1,
    'uibuttongroup': 1,
    'uicontextmenu': 1,
    'uicontrol': 1,
    'uigetdir': 1,
    'uigetfile': 1,
    'uigetpref': 1,
    'uiimport': 1,
    'uimenu': 1,
    'uint16': 1,
    'uint32': 1,
    'uint64': 1,
    'uint8': 1,
    'uiopen': 1,
    'uipanel': 1,
    'uipushtool': 1,
    'uiputfile': 1,
    'uiresume': 1,
    'uisave': 1,
    'uisetcolor': 1,
    'uisetfont': 1,
    'uisetpref': 1,
    'uistack': 1,
    'uitab': 1,
    'uitabgroup': 1,
    'uitable': 1,
    'uitoggletool': 1,
    'uitoolbar': 1,
    'uiwait': 1,
    'uminus': 1,
    'undocheckout': 1,
    'unicode2native': 1,
    'union': 1,
    'unique': 1,
    'unix': 1,
    'unloadlibrary': 1,
    'unmesh': 1,
    'unmkpp': 1,
    'unregisterallevents': 1,
    'unregisterevent': 1,
    'unstack': 1,
    'untar': 1,
    'unwrap': 1,
    'unzip': 1,
    'uplus': 1,
    'upper': 1,
    'urlread': 1,
    'urlwrite': 1,
    'usejava': 1,
    'userpath': 1,
    'validateattributes': 1,
    'validatestring': 1,
    'values': 1,
    'vander': 1,
    'var': 1,
    'varargin': 1,
    'varargout': 1,
    'varfun': 1,
    'vectorize': 1,
    'ver': 1,
    'verLessThan': 1,
    'verctrl': 1,
    'version': 1,
    'vertcat': 1,
    'vertexAttachments': 1,
    'vertexNormal': 1,
    'view': 1,
    'viewmtx': 1,
    'visdiff': 1,
    'volume': 1,
    'volumebounds': 1,
    'voronoi': 1,
    'voronoiDiagram': 1,
    'voronoin': 1,
    'wait': 1,
    'waitbar': 1,
    'waitfor': 1,
    'waitforbuttonpress': 1,
    'warndlg': 1,
    'warning': 1,
    'waterfall': 1,
    'wavfinfo': 1,
    'wavplay': 1,
    'wavread': 1,
    'wavrecord': 1,
    'wavwrite': 1,
    'web': 1,
    'weboptions': 1,
    'webread': 1,
    'websave': 1,
    'week': 1,
    'weekday': 1,
    'what': 1,
    'whatsnew': 1,
    'which': 1,
    'whitebg': 1,
    'who': 1,
    'whos': 1,
    'width': 1,
    'wilkinson': 1,
    'winopen': 1,
    'winqueryreg': 1,
    'withNoPlugins': 1,
    'withTextOutput': 1,
    'withVerbosity': 1,
    'workspace': 1,
    'write': 1,
    'writeDirectory': 1,
    'writeEncodedStrip': 1,
    'writeEncodedTile': 1,
    'writeVideo': 1,
    'writetable': 1,
    'xlabel': 1,
    'xlim': 1,
    'xlsfinfo': 1,
    'xlsread': 1,
    'xlswrite': 1,
    'xmlread': 1,
    'xmlwrite': 1,
    'xor': 1,
    'xslt': 1,
    'year': 1,
    'years': 1,
    'ylabel': 1,
    'ylim': 1,
    'ymd': 1,
    'yyyymmdd': 1,
    'zeros': 1,
    'zip': 1,
    'zlabel': 1,
    'zlim': 1,
    'zoom': 1
}

# Utility functions.
# .............................................................................

def matlab_function_or_command(name):
    return name in matlab_symbols



# Not using this now, but at some point we'll probably want to pick this up
# and make this scheme work.
#
# Table of known return types.
#
# 0 => returns a scalar
# 1 => returns an array
# 2 => scalar if given single argument of '1', array otherwise
#
# matlab_functions = {
#     'cell': 1,
#     'struct': 1,
#     'size': 1,
#     'null': 1,
#     'zeros': 2,
#     'diag': 0,
#     'repmat': 1
#     'magic': 2,
#     'meshgrid': 0,
#     'ones': 2,
#     'det': 0,
#     'str2num': 0
# }
