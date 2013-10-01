import os

def files_from(paths, recursive = False, validator=None):
    """
    Description:
        Return a generator for files contained in a list
        of files or directories.

    Parameters:
        paths: A list of files(strings), representing files
               or directories to be searched.

        validator: Function to validate if a given file is inserted
                   in the list of files to be returned.

                   This function take a file path as parameter and
                   return True if the file should be inserted in the
                   list, False otherwise.

        recursive: Boolean representing if directories need to be searched
                   recursively.
    """
    if not hasattr(paths, '__iter__'):
        paths = [paths]
    
    if not validator:
        validator = lambda _: True

    for path in paths:
        if not path:
            break
        if os.path.isfile(path):
            if validator(path):
                yield path
        elif os.path.isdir(path):
            for file in files_from_dir(path, recursive, validator):
                yield file

def files_from_dir(path, recursive = False, validator=None):
    """
    Description:
        Return a generator (iterator) for files contained in a directory.

    Parameters:
        path: A string representing a path to directory
              to be searched.

        validator: Function to validate if a given file is inserted
                   in the list of files to be returned.
                   This function take a file path as parameter and
                   return True if the file should be inserted in the
                   list, False otherwise.

        recursive: Boolean representing if directory need to be searched
                   recursively.
    """

    if not validator:
        validator = lambda _: True

    for dirpath, _, filenames in os.walk(path):
        files  = (os.path.join(dirpath, filename)
                  for filename in filenames if validator(os.path.join(dirpath, filename)))

        for file in files:
            yield file

        # do just the first iteration
        if not recursive: return
