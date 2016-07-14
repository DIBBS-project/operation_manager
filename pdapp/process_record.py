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


def set_variables(process_def, process_impl, parameters):
    pattern = re.compile(r'\$\{(.*)\}')

    for i in range(len(process_def.argv)):
        process_def.argv[i] = replace_all_occurrences(process_def.argv[i], pattern, parameters)

    for env in process_impl.environment:
        process_impl.environment[env] = replace_all_occurrences(process_impl.environment[env], pattern, parameters)

    if process_def.output_type == u'file':
        if u'file_path' in process_def.output_parameters:
            process_def.output_parameters[u'file_path']\
                = replace_all_occurrences(
                process_def.output_parameters[u'file_path'],
                    pattern,
                    parameters
                )

    return (process_def, process_impl)


def fileneames_dictionary(files):
    rfiles = {}
    for key in files:
        rfiles[key] = u'__file_' + key
    return rfiles


def set_files(process_def, process_impl, filenames):
    pattern = re.compile(r'@\{(.*)\}')

    for i in range(len(process_def.argv)):
        process_def.argv[i] = replace_all_occurrences(process_def.argv[i], pattern, filenames)

    for env in process_impl.environment:
        process_impl.environment[env] = replace_all_occurrences(process_impl.environment[env], pattern, filenames)

    return (process_def, process_impl)


def get_bash_script(process_def, process_impl, files, fileneames):
    script = u''

    for env in process_impl.environment:
        script += u'export ' + env + u'=' + process_impl.environment[env] + u'\n'

    if process_impl.cwd is not u'':
        script += u'\ncd ' + process_impl.cwd + u'\n'

    if process_impl.archive_url is not None and process_impl.archive_url is not "":
        script += u'\ncurl ' + process_impl.archive_url + u' > __archive.tar.gz\n' +\
                  u'tar -xzf __archive.tar.gz\n' +\
                  u'rm -f __archive.tar.gz\n'

    if files != {}:
        script += u'\n'
        for key in files:
            script += u'curl ' + files[key] + u' > ' + fileneames[key] + u'\n'

    script += u'\n' + process_impl.executable
    for arg in process_def.argv:
        script += u' ' + arg
    script += u'\n'

    return script
