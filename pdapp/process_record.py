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

    for i in range(len(record[u'argv'])):
        record[u'argv'][i] = replace_all_occurrences(record[u'argv'][i], pattern, parameters)

    for env in record[u'environment']:
        record[u'environment'][env] = replace_all_occurrences(record[u'environment'][env], pattern, parameters)

    if u'output_adapter' in record:
        if record[u'output_adapter'][u'output_type'] == u'file':
            if u'file_path' in record[u'output_adapter'][u'output_parameters']:
                record[u'output_adapter'][u'output_parameters'][u'file_path']\
                    = replace_all_occurrences(
                        record[u'output_adapter'][u'output_parameters'][u'file_path'],
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

    for i in range(len(record[u'argv'])):
        record[u'argv'][i] = replace_all_occurrences(record[u'argv'][i], pattern, filenames)

    for env in record[u'environment']:
        record[u'environment'][env] = replace_all_occurrences(record[u'environment'][env], pattern, filenames)

    return record


def get_bash_script(record, archive_url, files, fileneames):
    script = u''

    for env in record[u'environment']:
        script += u'export ' + env + u'=' + record[u'environment'][env] + u'\n'

    if u'cwd' in record:
        script += u'\ncd ' + record[u'cwd'] + u'\n'

    if archive_url is not None and archive_url is not "":
        script += u'\ncurl ' + archive_url + u' > __archive.tar.gz\n' +\
                  u'tar -xzf __archive.tar.gz\n' +\
                  u'rm -f __archive.tar.gz\n'

    if files != {}:
        script += u'\n'
        for key in files:
            script += u'curl ' + files[key] + u' > ' + fileneames[key] + u'\n'

    script += u'\n' + record[u'exec']
    for arg in record[u'argv']:
        script += u' ' + arg
    script += u'\n'

    return script
