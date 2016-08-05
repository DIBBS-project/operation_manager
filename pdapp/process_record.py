import re


def replace_index(string, first, last, newsubstr):
    newstr = ''
    if first != 0:
        newstr = string[:first]
    newstr = newstr + newsubstr
    if last < len(string):
        newstr += string[last:]
    return newstr


def replace_all_occurrences(string, pattern, parameters):
    for match in reversed(list(pattern.finditer(string))):
        param_name = match.group(1)
        if param_name in parameters:
            string = replace_index(string, match.start(0), match.end(0), parameters[param_name])
    return string


def set_variables(process_impl, parameters):
    pattern = re.compile(r'!\{([^\}]*)\}')

    process_impl.script = replace_all_occurrences(process_impl.script, pattern, parameters)

    if process_impl.output_type == u'file':
        if u'file_path' in process_impl.output_parameters:
            process_impl.output_parameters[u'file_path']\
                = replace_all_occurrences(
                process_impl.output_parameters[u'file_path'],
                    pattern,
                    parameters
                )


def fileneames_dictionary(files):
    rfiles = {}
    for key in files:
        rfiles[key] = u'__file_' + key
    return rfiles


def set_files(process_impl, filenames):
    pattern = re.compile(r'@\{([^\}]*)\}')

    process_impl.script = replace_all_occurrences(process_impl.script, pattern, filenames)


def get_bash_script(process_impl, files, fileneames):
    script = u''

    if process_impl.cwd is not u'':
        script += u'\ncd ' + process_impl.cwd + u'\n'

    if files != {}:
        script += u'\n'
        for key in files:
            script += u'curl ' + files[key] + u' > ' + fileneames[key] + u'\n'

    script += u'\n' + process_impl.script + u'\n'

    return script
