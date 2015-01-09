#!/usr/bin/env python

"""Codesign utility"""

import argparse
import subprocess
import os
import shutil
import json

parser = argparse.ArgumentParser( description = 'Codesign utility for Ninja builds' )
parser.add_argument( 'file',
                     type=str,
                     help = 'Bundle/package to sign' )
parser.add_argument( '--target',
                     help = 'Target',
                     choices = [ 'macosx', 'ios', 'android' ],
                     default = [] )
parser.add_argument( '--bundle',
                     help = 'Bundle identifier (OSX/iOS)',
                     default = [] )
parser.add_argument( '--organisation',
                     help = 'Organisation identifier (OSX/iOS)',
                     default = [] )
parser.add_argument( '--binname',
                     help = 'Binary name (OSX/iOS)',
                     default = [] )
parser.add_argument( '--prefs', type=str,
                     help = 'Preferences file',
                     default = [] )
parser.add_argument( '--builddir', type=str,
                     help = 'Build directory',
                     default = [] )
options = parser.parse_args()

androidprefs = {}
iosprefs = {}
macosxprefs = {}


def parse_prefs( prefsfile ):
  global androidprefs
  global iosprefs
  global macosxprefs
  if not os.path.isfile( prefsfile ):
    return
  file = open( prefsfile, 'r' )
  prefs = json.load( file )
  file.close()
  if 'android' in prefs:
    androidprefs = prefs['android']
  if 'ios' in prefs:
    iosprefs = prefs['ios']
  if 'macosx' in prefs:
    macosxprefs = prefs['macosx']


def codesign_ios():
  if not 'organisation' in iosprefs:
    iosprefs['organisation'] = options.organisation
  if not 'bundleidentifier' in iosprefs:
    iosprefs['bundleidentifier'] = options.bundle

  sdkdir = subprocess.check_output( [ 'xcrun', '--sdk', 'iphoneos', '--show-sdk-path' ] ).strip()
  entitlements = os.path.join( sdkdir, 'Entitlements.plist' )
  plistpath = os.path.join( options.builddir, 'Entitlements.xcent' )

  platformpath = subprocess.check_output( [ 'xcrun', '--sdk', 'iphoneos', '--show-sdk-platform-path' ] ).strip()
  localpath = platformpath + "/Developer/usr/bin:/Applications/Xcode.app/Contents/Developer/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin"
  plutil = "PATH=" + localpath + " " + subprocess.check_output( [ 'xcrun', '--sdk', 'iphoneos', '-f', 'plutil' ] ).strip()

  shutil.copyfile( entitlements, plistpath )
  os.system( plutil + ' -convert xml1 ' + plistpath )

  f = open( plistpath, 'r' )
  lines = [ line.strip( '\n\r' ) for line in f ]
  f.close()

  for i in range( 0, len( lines ) ):
    if lines[i].find( '$(AppIdentifierPrefix)' ) != -1:
      lines[i] = lines[i].replace( '$(AppIdentifierPrefix)', iosprefs['organisation'] + '.' )
    if lines[i].find( '$(CFBundleIdentifier)' ) != -1:
      lines[i] = lines[i].replace( '$(CFBundleIdentifier)', iosprefs['bundleidentifier'] )
    if lines[i].find( '$(binname)' ) != -1:
      lines[i] = lines[i].replace( '$(binname)', options.binname )

  with open( plistpath, 'w' ) as plist_file:
    for line in lines:
      plist_file.write( line + '\n' )
    plist_file.close()

  os.system( plutil + ' -convert binary1 ' + plistpath )
  os.system( '/usr/bin/codesign --force --sign ' + iosprefs['signature'] + ' --entitlements ' + plistpath + ' ' + options.file )


def codesign_macosx():
  sdkdir = subprocess.check_output( [ 'xcrun', '--sdk', 'macosx', '--show-sdk-path' ] ).strip()
  entitlements = os.path.join( sdkdir, 'Entitlements.plist' )


def codesign_android():
  pass


parse_prefs( options.prefs )

if options.target == 'ios':
  codesign_ios()
elif options.target == 'macosx':
  codesign_macosx()
elif options.target == 'android':
  codesign_android()
