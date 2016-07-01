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


def set_variables(record, parameters):
    pattern = re.compile(r'\$\{(.*)\}')

    for i in range(len(record.argv)):
        record.argv[i] = replace_all_occurrences(record.argv[i], pattern, parameters)

    for env in record.environment:
        record.environment[env] = replace_all_occurrences(record.environment[env], pattern, parameters)

    if record.output_type == u'file':
        if u'file_path' in record.output_parameters:
            record.output_parameters[u'file_path']\
                = replace_all_occurrences(
                record.output_parameters[u'file_path'],
                    pattern,
                    parameters
                )

    return record


def fileneames_dictionary(files):
    rfiles = {}
    for key in files:
        rfiles[key] = u'__file_' + key
    return rfiles


def set_files(record, filenames):
    pattern = re.compile(r'@\{(.*)\}')

    for i in range(len(record.argv)):
        record.argv[i] = replace_all_occurrences(record.argv[i], pattern, filenames)

    for env in record.environment:
        record.environment[env] = replace_all_occurrences(record.environment[env], pattern, filenames)

    return record


def get_bash_script(record, files, fileneames):
    script = u''

    for env in record.environment:
        script += u'export ' + env + u'=' + record.environment[env] + u'\n'

    if record.cwd is not u'':
        script += u'\ncd ' + record.cwd + u'\n'

    if record.archive_url is not None and record.archive_url is not "":
        script += u'\ncurl ' + record.archive_url + u' > __archive.tar.gz\n' +\
                  u'tar -xzf __archive.tar.gz\n' +\
                  u'rm -f __archive.tar.gz\n'

    if files != {}:
        script += u'\n'
        for key in files:
            script += u'curl ' + files[key] + u' > ' + fileneames[key] + u'\n'

    script += u'\n' + record.executable
    for arg in record.argv:
        script += u' ' + arg
    script += u'\n'

    return script
