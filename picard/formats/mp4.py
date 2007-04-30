# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from mutagen.mp4 import MP4
from picard.file import File
from picard.metadata import Metadata
from picard.util import encode_filename

class MP4File(File):
    EXTENSIONS = [".m4a", ".m4b", ".m4p", ".mp4"]
    NAME = "MPEG-4 Audio"

    __text_tags = {
        "\xa9ART": "artist",
        "\xa9nam": "title",
        "\xa9alb": "album",
        "\xa9wrt": "composer",
        "aART": "albumartist",
        "\xa9grp": "grouping",
        "\xa9day": "date",
        "\xa9gen": "genre",
        "\xa9lyr": "lyrics",
        "\xa9too": "encodedby",
        "\xa9lyr": "lyrics",
        "cprt": "copyright",
        "soal": "albumsort",
        "soaa": "albumartistsort",
        "soar": "artistsort",
        "sonm": "titlesort",
        "soco": "composersort",
        "sosn": "showsort",
        "tvsh": "show",
        "purl": "podcasturl",
    }
    __r_text_tags = dict([(v, k) for k, v in __text_tags.iteritems()])

    __bool_tags = {
        "pcst": "podcast",
        "cpil": "compilation",
        "pgap": "gapless",
    }
    __r_bool_tags = dict([(v, k) for k, v in __bool_tags.iteritems()])

    __freeform_tags = {
        "----:com.apple.iTunes:MusicBrainz Track Id": "musicbrainz_trackid",
        "----:com.apple.iTunes:MusicBrainz Artist Id": "musicbrainz_artistid",
        "----:com.apple.iTunes:MusicBrainz Album Id": "musicbrainz_albumid",
        "----:com.apple.iTunes:MusicBrainz Album Artist Id": "musicbrainz_albumartistid",
        "----:com.apple.iTunes:MusicIP PUID": "musicip_puid",
        "----:com.apple.iTunes:MusicBrainz Album Status": "releasestatus",
        "----:com.apple.iTunes:MusicBrainz Album Release Country": "releasecountry",
        "----:com.apple.iTunes:MusicBrainz Album Type": "releasetype",
        "----:com.apple.iTunes:MusicBrainz Disc Id": "musicbrainz_discid",
        "----:com.apple.iTunes:MusicBrainz TRM Id": "musicbrainz_trmid",
    }
    __r_freeform_tags = dict([(v, k) for k, v in __freeform_tags.iteritems()])

    def _load(self):
        file = MP4(encode_filename(self.filename))

        metadata = Metadata()
        for name, values in file.tags.items():
            if name in self.__text_tags:
                for value in values:
                    metadata.add(self.__text_tags[name], value)
            elif name in self.__bool_tags:
                metadata.add(self.__bool_tags[name], values and '1' or '0')
            elif name in self.__freeform_tags:
                for value in values:
                    value = value.strip("\x00").decode("utf-8", "replace")
                    metadata.add(self.__freeform_tags[name], value)
            elif name == "trkn":
                metadata["tracknumber"] = str(values[0][0])
                metadata["totaltracks"] = str(values[0][1])
            elif name == "disk":
                metadata["discnumber"] = str(values[0][0])
                metadata["totaldiscs"] = str(values[0][1])
            elif name == "covr":
                for value in values:
                    metadata.add("~artwork", (None, value))

        self.metadata.update(metadata)
        self._info(file)

    def _save(self):
        file = MP4(encode_filename(self.filename))

        if self.config.setting["clear_existing_tags"]:
            file.tags.clear()

        for name, values in self.metadata.rawitems():
            if name in self.__r_text_tags:
                file.tags[self.__r_text_tags[name]] = values
            elif name in self.__r_bool_tags:
                file.tags[self.__r_bool_tags[name]] = (values[0] == '1')
            elif name in self.__r_freeform_tags:
                values = [v.encode("utf-8") for v in values]
                file.tags[self.__r_freeform_tags[name]] = values

        if "tracknumber" in self.metadata:
            if "totaltracks" in self.metadata:
                file.tags["trkn"] = [(int(self.metadata["tracknumber"]),
                                      int(self.metadata["totaltracks"]))]
            else:
                file.tags["trkn"] = [(int(self.metadata["tracknumber"]), 0)]

        if "discnumber" in self.metadata:
            if "totaldiscs" in self.metadata:
                file.tags["disk"] = [(int(self.metadata["discnumber"]),
                                      int(self.metadata["totaldiscs"]))]
            else:
                file.tags["disk"] = [(int(self.metadata["discnumber"]), 0)]

        file.save()

    def supports_tag(self, name):
        return name in self.__r_text_tags or name in self.__r_bool_tags or name in self.__r_freeform_tags

