# Yasmine-CLI 

yasmine-cli is a command-line script for merging/editing stationxml files.


## Installation

### Requirements

    obspy >= 1.2
    pyyaml

These requirements should be automatically installed for you (see below).

### Before installing the code

Optionally, before installing the code, create a new python environment and activate it, e.g.,:

      >conda create -n yasmine_test python=3.8
      >conda activate yasmine_test

**Note:** In an empty python environment, installing yasmine-cli will trigger the
installation of any dependent packages that are missing, including obspy, numpy,
scipy and matplotlib.  Because yasmine-cli contains code that uses
matplotlib's backend to generate response plots, it is necessary to
have a suitable backend plotting package, which matplotlib does not
install by default. Trying to run yasmine-cli without a backend
installed will likely end in failure.

More information, including a list of supported matplotlib backends can be found at:

https://matplotlib.org/stable/tutorials/introductory/usage.html#backends

The backend I like to use can be installed via:

    >pip install pyqt5

### Installing yasmine-cli

There are a few different ways to obtain and install the code.

1. The easiest way is to install the latest version from pypi.org

https://pypi.org/project/yasmine-cli

  
    >pip install yasmine-cli


2. You can manually download the latest python wheel (*.whl) or distribution (*.gz) from:

https://gitlab.isti.com/mhagerty/yasmine-cli/-/package_files/3/download

and then install using pip:

    >pip install yasmine_cli-0.0.5-py2.py3-none-any.whl

Note that the version number may change.
Current version is 0.0.5 (major.minor.patch)


3. Install directly from github repository:

  e.g.,

      >pip install git+https://github.com/iris-edu/yasmine-stationxml-cli.git



### Usage

Once you have installed it, you should be able to run it as a python module from any directory.

    >yasmine-cli

     usage: yasmine-cli   [-h]
                          [--infiles // comma separated list of input xml files]
                          [--action [add/delete/update/select basenode] or
                          [default=update node attribute]]
                          ...

### Configuration and Logging

Currently, the only thing configurable outside of the command line
options pertains to logging:

    >cat config.yml

     LOG_DIR: some_path/to_my/log
     LOG_LEVEL: WARNING

yasmine-cli will look for the config.yml first in your current dir (from
where you are executing the cmd) and second in the yasmine-cli install
dir.  If it doesn't find a config.yml in either location, it will
default to:

     LOG_DIR: .
     LOG_LEVEL: INFO

Regardless of whether or not it finds a config.yml file, you can
override the LOG_LEVEL with the command line option:

    >yasmine-cli ... --loglevel=ERROR ...


## How It Works

An ObsPy Inventory object is essentially a container for a list of
Networks and each of these is a container for a list of Stations, etc.

yasmine-cli reads the input StationXML files into an Inventory object
which is then reorganized into a Python dictionary which is indexed
by searchable fields (e.g., station_code, channel_code).

At the bottom of this dictionary are lists of Station(s) (=station epochs) which in
turn contain Channel(s) (=channel epochs), and each of these is sorted
alphabetically and chronologically.


### Filtering to find the right level [default=root]

In order to decide which element(s) the action (described below) should apply to,
yasmine-cli looks at two flags:
 1. --level_{network, station, channel} [default=root]
 2. --station_epoch=int or --channel_epoch=int  // used when finer grain control is desired

The level flags (--level_network, --level_station, --level_channel) are
mutually exclusive. Which one you select depends on what level the
action should operate on. 

Each one takes a slightly different form, e.g.,

    --level_network=IU (act on this network)
    --level_network=*  (act on all networks)

    --level_station=IU.ANMO  (act on this station)
    --level_station=*.ANMO  (act on this station in all networks)
    --level_station=IU.*  (act on all stations in this network)
    --level_station=*.*  (act on all stations in all networks)

    --level_channel=IU.ANMO.00.BHZ  (act on this channel)
    --level_channel=IU.ANMO.00.*    (act on all channels at this location_code)
    --level_channel=IU.ANMO.*.*     (act on all channels at all location_codes)
    --level_channel=IU.*.*.*        (act on all channels of all stns of this network)
    --level_channel=*.*.*.*         (act on all channels of all stns of all networks)


Internally, the flags are used to set the 'scnl_filter' (really NSLC
since network.station.location.chanel, but anyway ...)

By default, if no --level_.. flag is set, the level is assumed to be "root" so that
any field you wish to modify must be part of the StationXML/Obspy_inventory root:
--field={source, sender, module, module_uri}.

### Actions to take [default=update or select]
yasmine-cli allows 4 basic actions: update, select, add, delete.

If no --action is specified, the action will default to **update** (if
--field and --value are specified) or to **select** (if not).

#### 1. --action=add 
In conjunction with --from_yml=/path/to/file.yml, this is
 used to insert a new basenode object (network, station or channel).

For example, to add a new network to the StationXML from a yaml file in ./yml/network.yml:

        >yasmine-cli --action=add --from_yml=./yml/network.yml --infiles=.. -o=.. 
        
Notice that it was not necessary to specify the --level_ in this case - A network can **only** go in the root
level and this is the default level.

Similarly, to add a new station to only the II network within a StationXML file:

        >yasmine-cli --action=add --level_network=II --from_yml=./yml/station.yml --infiles=.. -o=.. 
where now the level must be set (--level_network=* indicates *all* networks).

#### 2. --action=delete

This is used to delete a basenode object(s) at the indicated level.

For example, to delete all the channels from station IU.ANMO:

        >yasmine-cli --action=delete --level_station=IU.ANMO 

#### 3. --action=select [default]

This is used to select basenode object(s) that match the SCNL indicated
by --level_.

To select (=filter all matching) stations where station.code == 'ANMO' and print to stdout:

        >yasmine-cli  --level_station=IU.ANMO --infiles=data/II.xml 
        
#### 4. --action=update [default]

This is used to update (or insert if missing) the value of a basenode field
(attribute).

Every update takes two fields: --field and --value. The various --level and --epoch flags will help you select which
basenode object you want to modify.

If the underlying type of the attribute is a simple type (e.g., double, int, string),
then you can set the value on the command line, eg:

    --field=code --value=STA1 --level_network=IU
    --field=latitude --value=45. --level_station=IU.ANMO
    --field=description --value='This is a station description' --level_station=*.*

If instead, the expected value is a complex type which is itself an ObsPy object, you can create it from
yaml using the **--value=yml:** prefix:

    --field=data_availability --value=yml:yml/dataavailability.yml --level_station=IU.ANMO

The yaml files should have structure that follows the method calls of
the corresponding ObsPy objects.

For instance,

    >cat yml/operator.yml
      Operator:
        agency: 'United States Geological Survey, USGS'
        contacts:
          - person:
              names:
                - 'Adam Ringler'
                - 'Tyler Storm'
              agencies:
                - 'Albuquerque Seismic Lab'
              emails:
                - 'aringler@usgs.gov'
              phones:
                - (508)555-5555
        website: http://google.com

Note: 'Operator' is capitalized (since this will be used to generate an
ObsPy Operator(), and the fields must match those needed for
successful initializing of the particular ObsPy object.

However, on the command line, all fields are lower-case, e.g:
--field=operator or --field=comments. 

To see all allowable command-line fields for each level, do:

    >yasmine-cli --show_fields

Here is another example of a BaseNodeType object to be added:

    > cat yml/channel.yml
      Channel:
        code: 'HN1'
        location_code: '30'
        description: 'This is an added channel'
        start_date: 2006-06-30T20:00:01.000000Z
        end_date:   2399-12-31T23:59:59.000000Z
        latitude:     34.945911
        longitude:  -106.457199
        elevation: 1820.0
        depth: 0.0
        azimuth: 90.0

Note that the file contains all of the required fields (code,
location_code, ..., depth) needed to initialize a Channel object,
as well as one optional field (azimuth).  The user can add as
many optional fields as desired, provided the names and types
correspond to those ObsPy is expecting for this object.

##### When the --field or --value is a list []

If the expected field/value is a list (e.g., ObsPy expects Station.comments =
[Comments]), then there are several scenarios, depending on syntax.

 - The field can be a list (e.g. field=operators) or a scalar (field=operators[2]) and this is the *target*.
 - The value can be a list (value=[Operator1,Operator2,..] or value=[]) or a scalar (value=Operator or value=None), and this is the *source*.

Here are the allowable combinations (yasmine-cli will complain if you
do something else):

1. List to List: Populate ANMO station epochs with Station.operators = list created
   from yaml

      --field=operators --value=yml:yml/operators.yml --level_station=*.ANMO

2. List to empty list: Delete Station.operators:

      --field=operators --value=[] --level_station=*.ANMO

3. List to scalar: Append a single operator (from yaml) to the end of the existing list:

      --field=operators --value=yml:yml/operator.yml --level_station=*.ANMO

4. Scalar to scalar: Replace a single item at operators[2] with new operator (from yaml):

      --field=operators[2] --value=yml:yml/operator.yml --level_station=*.ANMO

5. Scalar to None: Delete operators[2] from the operators list:

      --field=operators[2] --value=None --level_station=*.ANMO


## Usage

    usage: yasmine-cli    [-h | --help]
                          [--level_network II | --level_station II.* | --level_channel II.ANMO.00.*]
                          [--action [add/delete/update basenode]]
                          [--epoch_station int] [--epoch_channel int]
                          [--field FIELD] [--value VALUE | --from_yml fname.yml]
                          [--infiles] [-o] [-p] [--print_all] [--dont_validate]
                          [--schema_version ver] [--show_fields] [--plot_resp]
                          [--plot_dir path]

    optional arguments:
      -h, --help            show this help message and exit

    level options: [default=root is implied if no level set]:
      --level_network II
      --level_station II.*
      --level_channel II.ANMO.00.*

    action options: [default=update if no action set]:
      --action [add/delete/update basenode]

    epoch options: Use to filter down to epoch level:
      --epoch_station int   station epoch index to filter on, eg, --epoch_station=1
      --epoch_channel int   channel epoch index to filter on, eg, --epoch_channel=0

    build options:
      --field FIELD         field, key or attribute to update. eg, --field=Latitude or --field=comments[1]
      --value VALUE         value of field, key or attribute to update. Ex.  --value=34.97 or --value=yml:/path/comment.yml
      --from_yml fname.yml  Used to add new basenode object created from
                            fname.yml. eg, --from_yml=/some/path/network.yml

    other optional arguments:
      --infiles             comma separated list of input xml files [default=stdin]
      -o , --output         Name of output xml file [default=stdout]. eg, --output=foo.xml
      -p, --print           Print out sorted Station/Channel epochs
      --print_all           Print out sorted Station/Channel epochs + operator/comment lists
      --dont_validate       Turn OFF StationXML validation on all inputs/outputs
      --schema_version ver  {1.0, 1.1}
      --show_fields         Print out allowable --field, + --value combinations
      --plot_resp           Plot all channel responses
      --plot_dir path       Path to dir to save plot responses
    
    Examples:
      >yasmine-cli --level_network=II --field=description --value='Network description' --infiles=...
      >yasmine-cli --level_station=II.* --field=latitude --value=34.97 --infiles=...
      >yasmine-cli --level_channel=II.ANMO.00.* --field=comments[0] --value=yml:/path/comment.yml --infiles=...
      >yasmine-cli --level_network=* --action=add --from_yml=path/to/station.yml --infiles=...
    

#### Some background on StationXML schema version and ObsPy
When ObsPy (v1.2)  moved to StationXML v1.1, they hard-coded the output xml version to 1.1.
We adapted ObsPy to allow the user to specify output xml version = 1.0.
However, ObsPy v1.2 is not strictly backwards compatible with StationXML
v1.0.
For instance, in fdsn schema 1.1, both Network and Station can
contain 0,..,n Operator elements, while in fdsn schema 1.0, only Station
can contain Operator elements. 

To understand how this affects the code, consider what happens when we
try to assign --field=operator to a network element when the input
StationXML version=1.0:

    (yasmine) mth@Mikes-MBP [~/mth/python_pkgs/yasmine-cli]> yasmine-cli --infiles=data/NE.xml --field=operators --value=yml:yml/operators.yml --level_network=* --schema_version=1.0 -o x.xml
    2020-03-19 15:00:00,766 [ INFO] Input schema_version=1.0
    2020-03-19 15:00:00,766 [ INFO] Input files version:[1.0] --> Request output version:[1.0]
    2020-03-19 15:00:00,766 [ INFO] Check file:data/NE.xml against schema_file:fdsn-schema/fdsn-station-1.0.xsd
    2020-03-19 15:00:07,362 [ INFO] _write_stationxml: set output schema_version=[1.0]
    Traceback (most recent call last):
      File "yasmine-cli.py", line 576, in <module>
        main()
      File "yasmine-cli.py", line 143, in main
    _write_stationxml(inv_new, outfile, validate=validate, schema_version=schema_version)
      File "/Users/mth/mth/python_pkgs/yasmine-cli/libs/libs_obs.py", line 226, in _write_stationxml
        raise Exception(msg)
    Exception: The created file fails to validate.
	    <string>:1:0:ERROR:SCHEMASV:SCHEMAV_ELEMENT_CONTENT: Element '{http://www.fdsn.org/xml/station/1}Operator': This element is not expected. Expected is one of ( {http://www.fdsn.org/xml/station/1}Comment, ##other{http://www.fdsn.org/xml/station/1}*, {http://www.fdsn.org/xml/station/1}TotalNumberStations, {http://www.fdsn.org/xml/station/1}SelectedNumberStations, {http://www.fdsn.org/xml/station/1}Station ).

Note that the log specifies which schema version it is using to validate
both the input and output xml files. Here, when we try to output the
modified StationXML (with network.operator), the validation fails as it
should.

The solution, if we want network.operator, is to specify that the output
schema version shall be 1.1:

    (yasmine) mth@Mikes-MBP [~/mth/python_pkgs/yasmine-cli]> yasmine-cli --infiles=data/NE.xml --field=operators --value=yml:yml/operators.yml --level_network=* --schema_version=1.1 -o x.xml
    2020-03-19 14:59:38,643 [ INFO] Input schema_version=1.0
    2020-03-19 14:59:38,643 [ INFO] Input files version:[1.0] --> Request output version:[1.1]
    2020-03-19 14:59:38,643 [ INFO] Check file:data/NE.xml against schema_file:fdsn-schema/fdsn-station-1.1.xsd
    2020-03-19 14:59:44,684 [ INFO] _write_stationxml: set output schema_version=[1.1]

Which works since StationXML v1.1 allows Network element to
contain Operator element (or network.operator in the language of ObsPy).


## More Examples

Plot channel responses:
  The following will pull only WES stations out of the input xml, will output the reduced stationxml to wes.xml and will output plots of all WES channels to ./zplot directory:

    >yasmine-cli --level_station=*.WES --infile=data/NE.xml --plot_resp --plot_dir=zplot -o wes.xml

(the default --plot_dir is ".")

Note that if --level_{network, station} is not specified, it will output plots of ALL channel responses.

The following will pull only xml related to one station (LJS1) and output to foo.xml:

    >yasmine-cli --infile=PRSMP-2020-04-01.xml -o foo.xml --level_station=*.LJS1

This could be used, for instance, to break up a network stationXML into smaller station stationXML files.

Note that the behavior is different if you specify --field and --value.
For instance, a similar command changes the station code from LJS1 to LJXX but outputs all stations
to the file foo.xml:

    >yasmine-cli --infile=PRSMP-2020-04-01.xml -o foo.xml --level_station=*.LJS1 --field=code --value='LJXX'

That is, these are 2 different actions, which could be explicitly specified on the command line:

    >yasmine-cli --action=select --infile=PRSMP-2020-04-01.xml -o foo.xml --level_station=*.LJS1
    >yasmine-cli --action=update --infile=PRSMP-2020-04-01.xml -o foo.xml --level_station=*.LJS1 --field=code --value='LJXX'

However, --action is not required in these cases since yasmine-cli will try to figure it out from the other params present.

Piping example:

  This example 1) Changes all ANMO station codes to 'MIKE', 2) Changes the
  latitude of all CCM stations to 33.77, 3) Adds list of operators to all
  MIKE stations, and 4) Replaces the 2nd operator in the list with a new
  operator from yml file:

      >cat TestX.xml | yasmine-cli --field=code --value=MIKE --level_station=*.ANMO --dont_validate | \
        yasmine-cli --field=latitude --value=33.77 --level_station=*.CCM | \
        yasmine-cli --field=operators --value=yml:yml/operators.yml --level_station=*.MIKE | \
        yasmine-cli --field=operators[1] --value=yml:yml/operator.yml --level_station=*.MIKE -o y.xml

  Note that when piping together executables as in: >run_A | run_B | run_C ,
  the OS does *not* run the executables in sequential order.
  e.g., it does not first run_A, then run_B, etc.
  Instead, all executables are essentially started at the same time and
  their inputs/outputs joined  by the pipes.
  While the end result will be as expected, the logfile may contain messages that
  appear to be out of order because of how shell piping works.
  e.g., you may see the messages for run_B *before* the messages for run_A.


Add a new Network

      >yasmine-cli --infiles=test.xml -o x.xml --action=add --from_yml=yml/network.yml --dont_validate

Set all Network code(s)

      >yasmine-cli --infiles=test.xml -o x.xml --field=code --value='XY' --level_network=*

Add a list operators = [Operator] (from yaml file) to this Network:

      >yasmine-cli --infiles=x.xml -o y.xml --field=operators --value=yml:yml/operators.yml --level_network=XY

Append a scalar Operator to this operators list (note operator.yml
contains one Operator):

      >yasmine-cli --infiles=y.xml -o z.xml --field=operators --value=yml:yml/operator.yml --level_network=XY

Replace the 2nd Operator with a new Operator (from yml):

      >yasmine-cli  --infiles=z.xml -o a.xml --field=operators[1] --value=yml:yml/operator.yml --level_network=XY

Delete the 1st Operator:

      >yasmine-cli  --infiles=z.xml -o a.xml --field=operators[0] --value=None --level_network=XY

Delete the entire operators list (note deleting a list is equivalent to
setting it to the empty list []):

      >yasmine-cli  --infiles=z.xml -o a.xml --field=operators --value=[] --level_network=XY

Add an operator to every station in network 'IU'.

      >yasmine-cli --infile=Test.xml --level_station=IU.* --action=add --from_yml=yml/operator.yml

Append a comment to every IU.ANMO channel epoch.

      >yasmine-cli --infile=TestX.xml --level_channel=*.ANMO.*.* --field=comments --value=yml:yml/comment.yml -o xx.xml 

Update latitude on all II.ANMO station.

      >yasmine-cli --infile=Test.xml --level_station=II.ANMO --field=latitude --value=75.12

Update latitude on all II.ANMO channel epochs.

      >yasmine-cli --infile=Test.xml --level_channel=II.ANMO.*.* --field=latitude --value=75.12

Replace the 7th comment of the 128th channel epoch of the 5th station
epoch with a comment from yaml file:

    >yasmine-cli --infiles=resources/ANMO.xml -o z.xml --field=comments[6] --value=yml:yml/comment.yml --level_channel=*.ANMO.10.VHZ --epoch_channel=128 --epoch_station=5

Delete the 3rd comment of the 128th channel epoch of the 5th station
epoch:

    >yasmine-cli --infiles=resources/ANMO.xml -o z.xml --field=comments[6] --value=yml:yml/comment.yml --level_channel=*.ANMO.10.VHZ --epoch_channel=128 --epoch_station=5

