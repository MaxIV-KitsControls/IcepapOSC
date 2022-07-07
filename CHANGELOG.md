# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [0.9.x]

### Added

 - The option to define curves from the command line (--sig) was not working 
 and now is fixed. 
 - The option to define curves from a file (--sigset) was not working and 
   now is fixed 
 - 2 more vertical axes are available to allow for more flexibility with 
   the autoranging when curves have too different ranges 
 - Scale and offset factors apply to all the acquired data (and not to only 
   from the point in time where they are set as before)
 - Scale and offset factors can be set from the command line call (--corr)
 - Ctrl+U allows to toggle whether the scale/offset factors are applied or not 
 - Measure curve differences between two points in time. Double click in 
   the graph fixes a second crosshair time location. Difference in the 
   curves between that crosshair and the crosshair that follows the mouse 
   are displayed in the top legend. 
 - Local min/max in the legend. The time range for the min/max curve values 
   in the legend is set by default to all acquired data. The time range can 
   be set to a local range by the following sequence: double-click as 
   described above to fix a cross-hair to one of the range-limits. Then 
   click on the time location for the other range. The min/max values in 
   the legend are updated for that local range only. A new click in the 
   data widget will reset the time range to all the acquired data. 
 - Ctrl+O allows to save directly to csv, the data within the time range 
   shown in the display (min/max in the legend are updated to that time 
   range as well). 
 - Ctrl+I allows to define a text string added to the name of the .csv file 
   saved via Ctrl+O 
 - Ctrl+A/Z/E load several predefined curves sets (experimental)


### Removed

### Fixed

## [0.8.2]

### Added
- Include button to add velocities curves.

### Removed

### Fixed
- Add Manifest to include Markdown and Licence files on the package
- Fix incompatibility with PyQt >= 5.12 (issue #22)
- Fix installation dependencies.

## [0.7.1]

### Added
- Application icon
- Add configuration for the signals set folder

### Removed
- Do backups: it was moved from icepap library to IcepapCMS as snapshots
- Status dialog: it will be implemented on the IcepapCMS console
- Esync button: it will be implemented on the IcepapCMS

### Fixed
- Load dynamically the UI files
- Add protection on the export signals settings
- Show axes labels on black background configuration
- Wrong windows opacity configuration does not allow to see the main windows 
  depending on the display configuration.

## [0.6.4]

### Added
- Allow to change the plot background.
- Allow to change color and form of the signal plotted.
- Add Trace Correction.
- Add axis control buttons.
- Import and Export signal set configuration to file.
- Allow to do backups

### Removed
- Button save to file
- Load dynamically the UI files

### Fixed


## [0.5.2] 

### Added
- Migrate to python 3
- Migrate to Qt 5
- Add protection to create configuration folders 
- Add the axis as optional parameter on the script. 

### Fixed
- Fix classifiers to upload to PyPi

## [0.4.0] 

### Added
- Allow to save on the file
- Allow to save the setting to a file

### Fixed


## [0.3.0] 

### Added
- Allow to set the signals from command line.

### Fixed

## [0.2.1] 

### Added
- Update setting dialog: allows to configure the axis X.
- Allows to change the port

### Fixed
- Fix bug in setting and adjusted dialogs.
- Remove the possibility to open two settings dialogs. 
- Do not allow to open more than one setting dialog

## [0.1.0] 

### Added
- First version of the Oscilloscope mode.

### Fixed

#
[keepachangelog.com]: http://keepachangelog.com
[0.1.0]: https://github.com/ALBA-Synchrotron/IcepapOCS/compare/0.1.0...0.2.0
[0.2.1]: https://github.com/ALBA-Synchrotron/IcepapOCS/compare/0.2.0...0.2.1
[0.3.0]: https://github.com/ALBA-Synchrotron/IcepapOCS/compare/0.2.1...0.3.0
[0.4.0]: https://github.com/ALBA-Synchrotron/IcepapOCS/compare/0.3.0...0.4.0
[0.5.2]: https://github.com/ALBA-Synchrotron/IcepapOCS/compare/0.4.0...0.5.2
[0.6.4]: https://github.com/ALBA-Synchrotron/IcepapOCS/compare/0.5.2...0.6.4
[0.7.1]: https://github.com/ALBA-Synchrotron/IcepapOCS/compare/0.6.4...0.7.1
[0.8.2]: https://github.com/ALBA-Synchrotron/IcepapOCS/compare/0.7.1...0.8.2
[0.9.x]: https://github.com/ALBA-Synchrotron/IcepapOCS/compare/0.8.2...HEAD

