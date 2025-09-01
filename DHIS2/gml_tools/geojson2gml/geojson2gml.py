import fileinput
import os
import subprocess
import time
from os import listdir
from os.path import isfile, join

input_dir = "input"
output_dir = "output"
shapefiles_dir = "shapefiles"


def main():
    is_csv = lambda fname: os.path.splitext(fname)[-1] in ['.geojson']
    is_not_csv = lambda fname: not os.path.splitext(fname)[-1] in ['.geojson']
    is_not_git = lambda fname: not fname.startswith(".git")
    applied_filter = is_not_git if is_csv else is_not_csv
    files = [f for f in filter(applied_filter, listdir(input_dir)) if isfile(join(input_dir, f))]

    for geojson_file in files:
        output_shapefile = geojson_file + '.shp'
        output_gml = geojson_file + ".gml"
        print("simplify boundaries of file " + geojson_file)
        args = ['mapshaper', '-i', join(input_dir, geojson_file), '-quiet', '-simplify', 'percentage=90%', '-o',
                join(output_dir, "simplified_" + geojson_file)]
        subprocess.Popen(args)
        time.sleep(200)
        print("convert to shapefile file " + join(output_dir, "simplified_" + geojson_file))
        args = ['ogr2ogr', '-f', 'ESRI Shapefile', join(shapefiles_dir, output_shapefile),
                join(output_dir, "simplified_" + geojson_file)]
        subprocess.Popen(args)
        time.sleep(200)

        print("convert to gml file" + join(shapefiles_dir, output_shapefile))
        args = ['ogr2ogr', '-f', 'GML', join(output_dir, output_gml), join(shapefiles_dir, output_shapefile)]
        subprocess.Popen(args)
        time.sleep(200)

        fout = open(join(output_dir, "dhis2_" + output_gml), "wt")

        with fileinput.FileInput(join(output_dir, output_gml), inplace=True) as file:
            for line in file:
                fout.write(line.replace("ogr:id>", "ogr:uid>"))

        file.close()
        fout.close()


if __name__ == '__main__':
    main()
