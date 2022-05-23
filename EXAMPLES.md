## More Examples

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

    (yasmine) mth@Mikes-MBP [~/mth/python_pkgs/yasmine-cli]> yasmine-cli --infiles=tests/test_data/NE.xml --field=operators --value=yml:yml/operators.yml --level_network='*' --schema_version=1.0 -o x.xml
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

    (yasmine) mth@Mikes-MBP [~/mth/python_pkgs/yasmine-cli]> yasmine-cli --infiles=tests/test_data/NE.xml --field=operators --value=yml:yml/operators.yml --level_network='*' --schema_version=1.1 -o x.xml
    2020-03-19 14:59:38,643 [ INFO] Input schema_version=1.0
    2020-03-19 14:59:38,643 [ INFO] Input files version:[1.0] --> Request output version:[1.1]
    2020-03-19 14:59:38,643 [ INFO] Check file:data/NE.xml against schema_file:fdsn-schema/fdsn-station-1.1.xsd
    2020-03-19 14:59:44,684 [ INFO] _write_stationxml: set output schema_version=[1.1]

Which works since StationXML v1.1 allows Network element to
contain Operator element (or network.operator in the language of ObsPy).
Alternatively, you may add the "--dont_validate" flag so that the code
does not try to validate the xml against the 1.0 FDSN schema.

#### Plot channel responses:
  The following will create response plots for each channel of station
WES and output them to the ./plot directory:

    >yasmine-cli --level_station='*.WES' --infile=tests/test_data/NE.xml --plot_resp --plot_dir=zplot

(the default --plot_dir is ".")

Note that if --level_{network, station} is not specified, it will output plots of ALL channel responses.

The following will pull only xml related to one station (LJS1) and output to foo.xml:

    >yasmine-cli --infile=tests/test_data/PRSMP-2020-04-01.xml -o foo.xml --level_station=*.LJS1

This could be used, for instance, to break up a network stationXML into smaller station stationXML files.

Note that the behavior is different if you specify --field and --value.
For instance, a similar command changes the station code from LJS1 to LJXX but outputs all stations
to the file foo.xml:

    >yasmine-cli --infile=tests/test_data/PRSMP-2020-04-01.xml -o foo.xml --level_station=*.LJS1 --field=code --value='LJXX'

That is, these are 2 different actions, which could be explicitly specified on the command line:

    >yasmine-cli --action=select --infile=tests/test_data/PRSMP-2020-04-01.xml -o foo.xml --level_station=*.LJS1
    >yasmine-cli --action=update --infile=tests/test_data/PRSMP-2020-04-01.xml -o foo.xml --level_station=*.LJS1 --field=code --value='LJXX'

However, --action is not required in these cases since yasmine-cli will try to figure it out from the other params present.

##### Piping example:

  This example 1) Changes all ANMO station codes to 'MIKE', 2) Changes the
  latitude of all CCM stations to 33.77, 3) Adds list of operators to all
  MIKE stations, and 4) Replaces the 2nd operator in the list with a new
  operator from yml file:

      >cat TestX.xml | yasmine-cli --field=code --value=MIKE --level_station='*.ANMO' --dont_validate | \
        yasmine-cli --field=latitude --value=33.77 --level_station='*.CCM' | \
        yasmine-cli --field=operators --value=yml:yml/operators.yml --level_station='*.MIKE' | \
        yasmine-cli --field=operators[1] --value=yml:yml/operator.yml --level_station='*.MIKE' -o y.xml

  Note that when piping together executables as in: >run_A | run_B | run_C ,
  the OS does *not* run the executables in sequential order.
  e.g., it does not first run_A, then run_B, etc.
  Instead, all executables are essentially started at the same time and
  their inputs/outputs joined  by the pipes.
  While the end result will be as expected, the logfile may contain messages that
  appear to be out of order because of how shell piping works.
  e.g., you may see the messages for run_B *before* the messages for run_A.


##### Add a new Network

      >yasmine-cli --infiles=test.xml -o x.xml --action=add --from_yml=yml/network.yml --dont_validate

##### Set all Network code(s)

      >yasmine-cli --infiles=test.xml -o x.xml --field=code --value='XY' --level_network=*

##### Add a list operators = [Operator] (from yaml file) to this Network:

      >yasmine-cli --infiles=x.xml -o y.xml --field=operators --value=yml:yml/operators.yml --level_network=XY

##### Append a scalar Operator to this operators list (note operator.yml contains one Operator):

      >yasmine-cli --infiles=y.xml -o z.xml --field=operators --value=yml:yml/operator.yml --level_network=XY

##### Replace the 2nd Operator with a new Operator (from yml):

      >yasmine-cli  --infiles=z.xml -o a.xml --field=operators[1] --value=yml:yml/operator.yml --level_network=XY

##### Delete the 1st Operator:

      >yasmine-cli  --infiles=z.xml -o a.xml --field=operators[0] --value=None --level_network=XY

##### Delete the entire operators list (note deleting a list is equivalent to setting it to the empty list []):

      >yasmine-cli  --infiles=z.xml -o a.xml --field=operators --value=[] --level_network=XY

##### Add an operator to every station in network 'IU'.

      >yasmine-cli --infile=Test.xml --level_station='IU.*' --action=add --from_yml=yml/operator.yml

##### Append a comment to every IU.ANMO channel epoch.

      >yasmine-cli --infile=TestX.xml --level_channel='*.ANMO.*.*' --field=comments --value=yml:yml/comment.yml -o xx.xml

##### Update latitude on all II.ANMO station.

      >yasmine-cli --infile=Test.xml --level_station=II.ANMO --field=latitude --value=75.12

##### Update latitude on all II.ANMO channel epochs.

      >yasmine-cli --infile=Test.xml --level_channel='II.ANMO.*.*' --field=latitude --value=75.12

##### Replace the 7th comment of the 128th channel epoch of the 5th station epoch with a comment from yaml file:

    >yasmine-cli --infiles=resources/ANMO.xml -o z.xml --field=comments[6] --value=yml:yml/comment.yml --level_channel='*.ANMO.10.VHZ' --epoch_channel=128 --epoch_station=5

##### Delete the 3rd comment of the 128th channel epoch of the 5th station epoch:

    >yasmine-cli --infiles=resources/ANMO.xml -o z.xml --field=comments[6] --value=yml:yml/comment.yml --level_channel='*.ANMO.10.VHZ' --epoch_channel=128 --epoch_station=5

##### If you need help figuring out how the station/channel epochs are numbered in your StationXML file:

    >yasmine-cli --infiles=tests/test_data/ANMO.xml -p           // Print out epochs

```[File:test_data/ANMO.xml]
  [Net:IU]
    [Stn:ANMO] epoch[0]:1989-08-29T00:00:00.000000Z - 1995-07-14T00:00:00.000000Z
      [Chn:BCI.--] epoch[0]:1989-08-29T00:00:00.000000Z - 1995-02-01T00:00:00.000000Z
      [Chn:BCI.--] epoch[1]:1995-02-01T00:00:00.000000Z - 1995-07-14T00:00:00.000000Z
      [Chn:BH1.--] epoch[2]:1995-03-28T21:15:00.000000Z - 1995-07-14T00:00:00.000000Z
      [Chn:BH2.--] epoch[3]:1995-03-28T21:15:00.000000Z - 1995-07-14T00:00:00.000000Z
      [Chn:BHE.--] epoch[4]:1989-08-29T00:00:00.000000Z - 1991-01-23T22:25:00.000000Z
      [Chn:BHE.--] epoch[5]:1991-01-23T22:25:00.000000Z - 1991-02-11T20:48:00.000000Z
      [Chn:BHE.--] epoch[6]:1991-02-11T20:48:00.000000Z - 1995-02-01T00:00:00.000000Z
      .
      .
      .
      [Chn:VWS.--] epoch[119]:1992-07-17T00:00:00.000000Z - 1995-02-01T00:00:00.000000Z
      [Chn:VWS.--] epoch[120]:1995-02-01T00:00:00.000000Z - 1995-07-14T00:00:00.000000Z
    [Stn:ANMO] epoch[1]:1995-07-14T00:00:00.000000Z - 2000-10-19T16:00:00.000000Z
      [Chn:BCI.--] epoch[0]:1995-07-14T00:00:00.000000Z - 1998-10-26T20:00:00.000000Z
      [Chn:BH1.--] epoch[1]:1995-07-14T00:00:00.000000Z - 1996-07-16T16:00:00.000000Z
      [Chn:BH1.--] epoch[2]:1996-07-29T00:00:00.000000Z - 1997-04-09T16:00:00.000000Z
      [Chn:BH1.--] epoch[3]:1997-04-09T16:00:00.000000Z - 1998-10-26T20:00:00.000000Z
      .
      .
      .
```
