def read_file(file_name):
    file = open(file_name, 'r', encoding='utf-8')
    file_content = file.read()
    file.close()
    return file_content
