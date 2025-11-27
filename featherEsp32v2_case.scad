// SPDX-License-Identifier: MIT
$fa = 1;
$fs = 0.4;

include <YAPP_Box/YAPPgenerator_v3.scad>

// Feather ESP32v2 case for Aluminum Tree Lights

printBaseShell = true;
printLidShell = true;

// 52.3mm x 22.8mm x 7.2mm per https://www.adafruit.com/product/5400
pcbLength = 52.3;
pcbWidth = 22.8;
pcbThickness = 7.2;

paddingLeft = 4;
paddingRight = 4;
paddingFront = 2;
paddingBack = 2;

wallThickness = 1.5;
basePlaneThickness = 1.5;
lidPlaneThickness = 1.5;

baseWallHeight = 15;
lidWallHeight = 10;

ridgeHeight = 5;
ridgeSlack = 0.2;
roundRadius = 2.0;

standoffHeight = 5.0;
standoffPinDiameter = 2;
standoffHoleSlack = 0.5;
standoffDiameter = 4;

pcbStands = [
   [2, 2, yappHole, yappBaseOnly, yappSelfThreading]
   ,[2, (pcbWidth - paddingRight) + 2, yappHole, yappBaseOnly, yappSelfThreading]
   ,[(pcbLength - (paddingFront + 2)), 2, yappHole, yappBaseOnly, yappSelfThreading]
   ,[(pcbLength - (paddingFront + 2)), (pcbWidth - paddingRight) + 2, yappHole, yappBaseOnly, yappSelfThreading]
   ];

cutoutsBack = [
   [ (7 - (paddingRight/2 - 1)) , -7, 11.42, 8.26, 0, yappRectangle]
   ];

cutoutsRight = [
   [pcbLength / 2, -7, 13, 7, 0, yappRectangle]
   ];


YAPPgenerate();