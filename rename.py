"""Rename

A simple tool for batch-renaming pictures to the date they were taken.

This renames every image file in the directory specified. Take care that you
don't have any files with names you care about, as there's no way to undo the
name change.

Usage:
    rename.py <path>
    rename.py --format <pattern> <path>

Options:
    -h, --help              Show this screen.
    -f, --format <pattern>  The pattern to use when renaming images. Reference:
                            http://strftime.org [default: %Y-%m-%d %H.%M.%S]
"""

import datetime
import imghdr
import os
import os.path

from docopt import docopt
import piexif

def is_image(path):
    # imghdr.what will try to open() whatever is passed to it, ensure `path`
    # isn't a directory so it doesn't error.
    if os.path.isfile(path) and imghdr.what(path):
        return True
    return False

class DateTimeOriginal:
    """DateTimeOriginal is the date that a photograph was taken.

    This is an EXIF tag typically set by your camera when you take a picture,
    but it can also be set manually (depending on operating system).

    This is the most reliable date for a photograph, as "date created" and "date
    modified" can change if a file is copied or saved, respectively.

    http://www.awaresystems.be/imaging/tiff/tifftags/privateifd/exif/datetimeoriginal.html
    """
    def __init__(self, exif):
        self.exif = exif

        # ID for the DateTimeOriginal tag stored in the Exif data.
        self.tag = 36867

        # The standard format that cameras save the date as.
        self.format = "%Y:%m:%d %H:%M:%S" # 2015:02:07 12:10:00

    def get_date(self):
        exif = self.exif["Exif"]
        if self.tag in exif:
            date = exif[self.tag].decode("utf-8")
            return datetime.datetime.strptime(date, self.format)

class File:
    """Generic class for handling file operations."""
    def __init__(self, path):
        # Setting these could also be done by simply calling self.set_path().
        # Opting for a more verbose approach so that you don't have to look to
        # another function to find exactly what properties this class has.
        self.path = path
        self.name = os.path.basename(path)
        self.dir = os.path.dirname(path)

    def has_sibling(self, file):
        """Checks if this File has `file` at the same path."""
        return os.path.exists(os.path.join(self.dir, file))

    def set_path(self, new_path):
        """Modifies all the path properties.

        This needs to be called every time the file's path is changed (i.e.
        after using os.rename) to keep the properties synced with the real file.
        """
        self.path = new_path
        self.name = os.path.basename(new_path)
        self.dir = os.path.dirname(new_path)

    def get_date_created(self):
        """Returns the date that the file was created.

        This is changed to the current date when a file is copied, so it might
        not be the exact date you're looking for.
        """
        creation_time = os.path.getctime(self.path)
        date_created = datetime.datetime.fromtimestamp(creation_time)
        return date_created

    def get_date_modified(self):
        """Returns the date that the file was last modified."""
        modification_time = os.path.getmtime(self.path)
        date_modified = datetime.datetime.fromtimestamp(modification_time)
        return date_modified

    def get_alternate_name(self, file):
        """Returns a new name for the file that doesn't currently exist.

        Sometimes you'll end up dealing with duplicate files, this method allows
        you to get a name for your duplicates so you can save them properly.
        """
        name, ext = os.path.splitext(file)
        existing_copies = 1
        while True:
            new_name = "%s (%s)%s" % (name, existing_copies, ext)
            if not self.has_sibling(new_name):
                return new_name
            existing_copies += 1

    def rename(self, new_name):
        extension = os.path.splitext(self.name)[1]
        new_name = new_name + extension
        new_path = os.path.join(self.dir, new_name)

        try:
            os.rename(self.path, new_path)
        except FileExistsError:
            new_name = self.get_alternate_name(new_name)
            new_path = os.path.join(self.dir, new_name)
            os.rename(self.path, new_path)
        finally:
            print("\"%s\" renamed to \"%s\"" % (self.name, new_name))
            self.path = new_path

class Photo(File):
    def __init__(self, path, date_format="%Y-%m-%d %H.%M.%S"):
        super().__init__(path)
        self.date_format = date_format

    def has_exif_data(self):
        """Checks if the photo has any EXIF data."""
        file_type = imghdr.what(self.path)
        # JPEG and TIFF are the only files that piexif supports.
        if file_type == "jpeg" or file_type == "tiff":
            return True
        return False

    def get_exif_data(self):
        """Returns the photos's EXIF data, if it exists."""
        if self.has_exif_data():
            return piexif.load(self.path)

    def get_date_taken(self):
        if self.has_exif_data():
            exif = self.get_exif_data()
            date_taken = DateTimeOriginal(exif)
            return date_taken.get_date()

    def get_earliest_date(self):
        """Returns the earliest date that the photo was taken."""
        date_taken = self.get_date_taken()
        date_modified = self.get_date_modified()
        date_created = self.get_date_created()

        # date_taken will only exist for JPEG and TIFF files, and even then
        # it's possible for the date to be missing. Ensure it exists before
        # comparing.

        if date_taken and date_taken < date_created:
            return date_taken.strftime(self.date_format)
        elif date_created < date_modified:
            return date_created.strftime(self.date_format)
        else:
            return date_modified.strftime(self.date_format)

def main():
    args = docopt(__doc__)

    for path, dirs, files in os.walk(args["<path>"]):
        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            if is_image(file_path):
                photo = Photo(file_path, date_format=args["--format"])
                photo.rename(photo.get_earliest_date())

if __name__ == "__main__":
    main()
