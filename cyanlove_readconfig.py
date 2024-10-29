import configparser


class readconfig:

    @staticmethod
    def write_ini_file(file_path, section, key, value):
        config = configparser.ConfigParser()

        # 添加新节和键值对
        if not config.has_section(section):
            config.add_section(section)

        config.set(section, key, value)

        with open(file_path, 'w') as configfile:
            config.write(configfile)

    @staticmethod
    def read_ini_file(file_path, section, key):
        config = configparser.ConfigParser()
        config.read(file_path)

        if config.has_section(section) and config.has_option(section, key):
            value = config.get(section, key)
            return value
        else:
            return None
