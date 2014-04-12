#!/usr/bin/perl -s

$help = $h;

$v=1 if ($verbose);

if (!$payload) {
    print "You MUST enter a payload weight!\n\n";
    $help = 1;
}

if (!$balloon) {
    print "You MUST enter a balloon mass!\n\n";
    $help = 1;
}

if (!$parachute) {
    print "You MUST enter a parachute diameter!\n\n";
    $help = 1;
}

if (!$helium) {
    print "You MUST enter the number of helium tanks!\n\n";
    $help = 1;
}


if (!$arl) {
    print "You MUST enter the name of an ARL file!\n\n";

    print "1. Go to: http://ready.arl.noaa.gov/READYcmet.php\n";
    print "\n";
    print "2. Enter a latitude and longitude. (negative lon for US...)\n";
    print "\n";
    print "3. Under \"Sounding\" drop-down, choose \"NAM Model (12 km over US) ...\"\n";
    print "\n";
    print "4. Meteorological Forecast Cycle: click \"next\"\n";
    print "\n";
    print "5. On \"Change Default Model Parameters and Display Options\" screen:\n";
    print "   a. Change time to plot to time closest to launch (Ann Arbor is 4 hours behind UTC - 15UTC is an 11AM EST launch)\n";
    print "   b. Change \"output options\" to \"TEXT ONLY\"\n";
    print "   c. Leave other options as defaults\n";
    print "   d. Enter captcha and click \"get sounding\"\n";
    print "\n";
    print "6. Copy data into a text program and save it. The name of the file is\n";
    print "irrelevant, but you need it for steps below (I will call the file\n";
    print "arl_example.txt, but I typically name the file arl_yyyymmdd.txt, where\n";
    print "yyyy = year, mm = two digit month, dd = two digit day).\n";
    print "\n";

    $help = 1;
}

if ($help) {
    print "./driver.pl options: \n";
    print "            -arl=arl_file.txt \n";
    print "            -balloon=mass of the balloon, acceptable values:\n";
    print "                     200, 300, 350, 450, 500, 600, 700, 800, \n";
    print "                     1000, 1200, 1500, 2000, 3000 \n";
    print "            -payload=WEIGHT of payload (in lbs) \n";
    print "            -parachute=diameter of parachute (in feet) \n";
    print "            -helium=tanks of helium (typically between 1-2) \n";
    print "            -ARLLatitude=Initial Latitude, if different from ARL file\n";
    print "            -ARLLongitude=Initial Longitude, if different from ARL file (negative for US!)\n";
    print "            -ARLAltitude=Initial Altitude, if different from ARL file \n";
    print "            -ascent calculate ascent rate\n";
    print "            -predict calculate balloon trajectory\n";
    print "            -callsign=call sign of person running code \n";
    print "            -burstheight=force burst altitude \n";
    print "            -bursttime=force burst time duration \n";
    print "            -cleanup will delete temporary files \n";

    exit(1);
}

$ARLLatitude  = -999 if (!$ARLLatitude);
$ARLLongitude = -999 if (!$ARLLongitude);
if (!$callsign) {
    $callsign=int(rand(10000));
}

$pi = 3.1415927;
$dtor = $pi/180.0;
$k = 1.3806503e-23;
$g = 9.8;
# Assume mass of 30 AMU.
$m = 30.0*1.67260e-27;

#$aprs = "aprsdata.txt" if (!$aprs);
$arl = "ARL.txt" if (!$arl);

$StartAltitude = 0.0 if (!$StartAltitude);

open(ARL,"<$arl");

$Done = 0;

while (!$Done) {

    $_ = <ARL>;

    if (/LAT..(.*)LON..(.*)ELEV.(.*)m/) {

	$ARLLatitude  = $1+0.0 if ($ARLLatitude  == -999);
	$ARLLongitude = $2+0.0 if ($ARLLongitude == -999);
	$ARLElevation = $3+0 if (!$ARLElevation);

	print "ARL Lat/Lon/Ele : $ARLLatitude deg, ";
	print "$ARLLongitude deg, $ARLElevation m\n";

    }

    if (/LAT..(.*)LON..(.*)/) {

	$ARLLatitude  = $1+0.0 if ($ARLLatitude  == -999);
	$ARLLongitude = $2+0.0 if ($ARLLongitude == -999);
	$ARLElevation = 0.0;

	print "ARL Lat/Lon/Ele : $ARLLatitude deg, ";
	print "$ARLLongitude deg, $ARLElevation m\n";

    }

    if (/Estimated/) {

	$Done = 1;
	$line = <ARL>;

	while (!($line=~/hysplit/)) {
	    $line = <ARL>;
	    if ($line=~/\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)/) {
		$Pressure    = $1+0.0;
		$Height      = $2+0.0;
		$Temperature = $3+0.0;
		$DewPoint    = $4+0.0;
		$Direction   = $5+0.0;
		$Speed       = $6+0.0;
		$Vn = $Speed * sin((270.0-$Direction)*$dtor);
		$Ve = $Speed * cos((270.0-$Direction)*$dtor);
		if ($v) {
                  print "ARL p/h/s: $Pressure $Height $Speed $Vn $Ve $DewPoint\n";
                }
		push(@ARLPressure, $Pressure);
		push(@ARLHeight, $Height);
		push(@ARLTemperature, $Temperature);
		push(@ARLDew, $DewPoint);
		push(@ARLVn, $Vn);
		push(@ARLVe, $Ve);
	    }
	}

    }

}

close(ARL);

if ($ARLLatitude == -999) {
    print "Can't find ARL latitude!  The code HAS to have this!\n";
    exit(2);
}

if ($ARLLongitude == -999) {
    print "Can't find ARL longitude!  The code HAS to have this!\n";
    exit(3);
}

$ARLLatitudeSave  = $ARLLatitude;
$ARLLongitudeSave = $ARLLongitude+360.0;
$ARLElevationSave = $ARLElevation;

# We want 3 negative ascent rates in a row to count as burst!

$Burst1 = 0;
$Burst2 = 0;
$Burst3 = 0;
$DidBurst = 0;

$CurrentLatitude = $ARLLatitude;
$CurrentLongitude = $ARLLongitude;
$CurrentElevation = $ARLElevation;

$FirstPoint = 1;
$OldTime = 0.0;

$StartTime = 0.0;

if ($aprs) {

    open(APRS,"<$aprs");
	print "opening aprs\n";
    while (<APRS>) {
	print "in aprs\n";
	if (/time.(\d+).*lat>(\S+)<.lat.*lng>(\S+)<.lng><alt>(\S+)<.alt>/) {

	    $UT = $1+0.0;
	    $Latitude = $2+0.0;
	    
#	    $LongitudeDeg = int(($3+0.0)/100.0);
#	    $LongitudeMin = (($3+0.0) - $LongitudeDeg*100.0);
#	    $Longitude = 360.0 - ($LongitudeDeg + $LongitudeMin/60.0);
	    $Longitude = 360.0 + $3;

	    $Altitude = $4+0.0;
		print $1." ".$2." ".$3." ".$4."\n";
	    if ($Altitude > 0 & $UT != $UTOld) {

		print "APRS t/l/l/a : $UT $Latitude $Longitude $Altitude\n";
		
		if ($LatitudeOld) {
		    $dt = $UT-$UTOld;

		    if ($dt < 0.0) {
			print "Bad Packet! (dt = $dt)\n";
		    } else {

		    # If this is a good packet, call it the current point:
			$CurrentLatitude = $Latitude;
			$CurrentLongitude = $Longitude;
			$CurrentElevation = $Altitude;

			print "$CurrentElevation\n";

			$dr = (6372000.0+$Altitude)*$dtor;
			$Correction = cos(($Latitude*$dtor));
			$Vn = ($Latitude-$LatitudeOld)/$dt * $dr;
			$Ve = ($Longitude-$LongitudeOld)/$dt*$dr*$Correction;

#		    print "Vn : $Latitude - $LatitudeOld / $dt * $dr = $Vn\n";

			$Vr = int(($Altitude-$AltitudeOld)/$dt*60.0); #ft/min

		    # This makes sure that the first point for prediction is
		    # the first point in the aprs file.  This could be bad,
		    # since it should show up as the SRB.  We probably
		    # want to do this a bit better.
			if (($Vr > 0) && ($FirstPoint)) {
			    $ARLLatitude = $Latitude;
			    $ARLLongitude = $Longitude-360.0;
			    $ARLElevation = $Altitude;
			    $StartTime = $UT;
			    $FirstPoint = 0;
			}

			if (($Vr < 0) && ($VrAve > 0)) {

			# To count as a burst, we want:
			# 1. the altitude to be above 10,000ft.
			# 2. 3 negative ascent rates in a row.

			    if ($burst3) {
				$a0 = $a0Save;
				$t0 = $t0Save;
				print "!!!!!! --->BURST<--- !!!!!! Alt: $a0\n";
				$DidBurst = 1;
			}
			    $burst3 = 1 if ($burst2);
			    $burst2 = 1 if ($burst1);
			    $burst1 = 1;

			    if (($burst1) && (!$burst2) && (!$burst3)) {
				$a0Save = $AltitudeOld;
				$t0Save = $UTOld;
			    }
			} 

		    # This resets the burst counter to 0 if we have a positive
		    # ascent rate and we have definitely NOT burst.
			if (($Vr > 0) && (!$burst3)) {
			    $burst1 = 0;
			    $burst2 = 0;
			    $burst3 = 0;
			}

			$VrAve = int(($Altitude - $a0)/($UT-$t0) * 60.0); #ft/min
			$Height = ($Altitude-$StartAltitude) * 0.3048;

#		    print "$Hour $Minute $Second Ascent Rate $Vr (ft/min); Ave : $VrAve (ft/min)\n";

#		    print "$Hour $Minute $Second $dt $Latitude $Longitude $Height $Vn $Ve $Vr\n";

			push(@APRSHeight, $Height);
			push(@APRSVn, $Vn);
			push(@APRSVe, $Ve);
			push(@APRSVr, $Vr);

			push(@APRSSpeed, sqrt($Vn*$Vn + $Ve*$Ve));

		    }
		}

		push(@APRSLatitude, $Latitude);
		push(@APRSLongitude, $Longitude);

		$LatitudeOld = $Latitude;
		$LongitudeOld = $Longitude;
		$AltitudeOld = $Altitude;
		$UTOld = $UT;

		$t0 = $UT if (!$t0);
		$a0 = $Altitude if (!$a0);

	    }
	
	}

    }
    #Convert to here in python



#    while (<APRS>) {
#
#	if (/(\d+)h(\S+)N.(\S+)W.*A=(\d+)/) {
#
#	    $Time = $1+0.0;
#	    $LatitudeDeg = int(($2+0.0)/100.0);
#	    $LatitudeMin = (($2+0.0) - $LatitudeDeg*100.0);
#	    $Latitude = $LatitudeDeg + $LatitudeMin/60.0;
#	    
#	    $LongitudeDeg = int(($3+0.0)/100.0);
#	    $LongitudeMin = (($3+0.0) - $LongitudeDeg*100.0);
#	    $Longitude = 360.0 - ($LongitudeDeg + $LongitudeMin/60.0);
#
#	    $Altitude = $4+0.0;
#
#	    if ($Altitude > 0) {
##	    print "APRS t/l/l/a : $Time $Latitude $Longitude $Altitude\n";
#		$Hour   = int($Time/10000);
#		$Minute = int(($Time-$Hour*10000)/100);
#		$Second = $Time-$Hour*10000 - $Minute*100;
#		$UT = $Hour*3600.0 + $Minute*60.0 + $Second;
#		if ($LatitudeOld) {
#		    $dt = $UT-$UTOld;
#
#		    if ($dt < 0.0) {
#			print "Bad Packet! (dt = $dt)\n";
#		    } else {
#
#		    # If this is a good packet, call it the current point:
#			$CurrentLatitude = $Latitude;
#			$CurrentLongitude = $Longitude;
#			$CurrentElevation = $Altitude;
#
#			$dr = (6372000.0+$Altitude)*$dtor;
#			$Correction = cos(($Latitude*$dtor));
#			$Vn = ($Latitude-$LatitudeOld)/$dt * $dr;
#			$Ve = ($Longitude-$LongitudeOld)/$dt*$dr*$Correction;
#
##		    print "Vn : $Latitude - $LatitudeOld / $dt * $dr = $Vn\n";
#
#			$Vr = int(($Altitude-$AltitudeOld)/$dt*60.0); #ft/min
#
#		    # This makes sure that the first point for prediction is
#		    # the first point in the aprs file.  This could be bad,
#		    # since it should show up as the SRB.  We probably
#		    # want to do this a bit better.
#			if (($Vr > 0) && ($FirstPoint)) {
#			    $ARLLatitude = $Latitude;
#			    $ARLLongitude = $Longitude-360.0;
#			    $ARLElevation = $Altitude;
#			    $FirstPoint = 0;
#			}
#
#			if (($Vr < 0) && ($VrAve > 0)) {
#
#			# To count as a burst, we want:
#			# 1. the altitude to be above 10,000ft.
#			# 2. 3 negative ascent rates in a row.
#
#			    if ($burst3) {
#				$a0 = $a0Save;
#				$t0 = $t0Save;
#				print "!!!!!! --->BURST<--- !!!!!! Alt: $a0\n";
#				$DidBurst = 1;
#			}
#			    $burst3 = 1 if ($burst2);
#			    $burst2 = 1 if ($burst1);
#			    $burst1 = 1;
#
#			    if (($burst1) && (!$burst2) && (!$burst3)) {
#				$a0Save = $AltitudeOld;
#				$t0Save = $UTOld;
#			    }
#			} 
#
#		    # This resets the burst counter to 0 if we have a positive
#		    # ascent rate and we have definitely NOT burst.
#			if (($Vr > 0) && (!$burst3)) {
#			    $burst1 = 0;
#			    $burst2 = 0;
#			    $burst3 = 0;
#			}
#
#			$VrAve = int(($Altitude - $a0)/($UT-$t0) * 60.0); #ft/min
#			$Height = ($Altitude-$StartAltitude) * 0.3048;
#
##		    print "$Hour $Minute $Second Ascent Rate $Vr (ft/min); Ave : $VrAve (ft/min)\n";
#
##		    print "$Hour $Minute $Second $dt $Latitude $Longitude $Height $Vn $Ve $Vr\n";
#
#			push(@APRSHeight, $Height);
#			push(@APRSVn, $Vn);
#			push(@APRSVe, $Ve);
#			push(@APRSVr, $Vr);
#
#			push(@APRSSpeed, sqrt($Vn*$Vn + $Ve*$Ve));
#
#		    }
#		}
#
#		$LatitudeOld = $Latitude;
#		$LongitudeOld = $Longitude;
#		$AltitudeOld = $Altitude;
#		$UTOld = $UT;
#
#		$t0 = $UT if (!$t0);
#		$a0 = $Altitude if (!$a0);
#
#	    }
#	
#	}
#
#    }

    close(APRS);

    if ($StartTime) {
	$dttotal = $UT-$StartTime;
    }

}

# Smooth over the APRS Data.  Let's try a median filter.

$iAPRS = 0;
foreach $aprsspeed(@APRSSpeed) {

    # First assume that the middle value is the median:
    $iMedian = $iAPRS;
    
    if (($iAPRS > 0) && ($iAPRS < scalar(@APRSSpeed)-1)) {

	# Choose the median of three values:

	if ((@APRSSpeed[$iAPRS-1] > @APRSSpeed[$iAPRS]) &&
	    (@APRSSpeed[$iAPRS-1] < @APRSSpeed[$iAPRS+1])) {
	    $iMedian = $iAPRS-1; }
	if ((@APRSSpeed[$iAPRS-1] < @APRSSpeed[$iAPRS]) &&
	    (@APRSSpeed[$iAPRS-1] > @APRSSpeed[$iAPRS+1])) {
	    $iMedian = $iAPRS-1; }
	if ((@APRSSpeed[$iAPRS+1] > @APRSSpeed[$iAPRS]) &&
	    (@APRSSpeed[$iAPRS+1] < @APRSSpeed[$iAPRS-1])) {
	    $iMedian = $iAPRS+1; }
	if ((@APRSSpeed[$iAPRS+1] < @APRSSpeed[$iAPRS]) &&
	    (@APRSSpeed[$iAPRS+1] > @APRSSpeed[$iAPRS-1])) {
	    $iMedian = $iAPRS+1; }

    }

    @APRSVn[$iAPRS] = @APRSVn[$iMedian];
    @APRSVe[$iAPRS] = @APRSVe[$iMedian];

    $iAPRS++;

}

# Let's overwrite the ARL data with APRS data.  To do this, we simply see
# if there is data between two ARL data points, find all of the APRS data
# in that height range, average it, and then overwrite the data.

$arlold = 0.0;

$iARL = 0.0;

foreach $arlheight(@ARLHeight) {

#    print "$arlheight $ARLVn[$iARL] $ARLVe[$iARL]\n";

    $i     = 0;
    $AveVn = 0.0;
    $AveVe = 0.0;
    $nPts  = 0;
	
    foreach $aprsheight(@APRSHeight) {

	if ($aprsheight > $arlold && $aprsheight < $arlheight) {
#	    print "aprs : $aprsheight, $APRSVn[$i], $APRSVe[$i]\n";
	    $AveVn += $APRSVn[$i];
	    $AveVe += $APRSVe[$i];
	    $nPts++;
	}
	$i++;

    }

    if ($nPts > 0) {
	$AveVn = $AveVn/$nPts;
	$AveVe = $AveVe/$nPts;
	#print "Aves : $AveVn $AveVe\n";
	$ARLVe[$iARL] = $AveVe;
	$ARLVn[$iARL] = $AveVn;
    }

    $arlold = $arlheight;
    $iARL++;

}

# Now, let's see if there is data above the maximum ARL height.  Average
# this, then calculate a new pressure, which is a bit tricky.

$maxarl = $arlold*3.28;
print "Max ARL Height  : $maxarl (feet)\n";

$iARL--;

$i     = 0;
$AveVn = 0.0;
$AveVe = 0.0;
$MaxHeight = 0.0;
$nPts  = 0;

foreach $aprsheight(@APRSHeight) {

    if ($aprsheight > $arlold) {
	$AveVn += $APRSVn[$i];
	$AveVe += $APRSVe[$i];
	$MaxHeight = $aprsheight if ($aprsheight > $MaxHeight);
	$nPts++;
    }
    $i++;

}

if ($nPts > 0) {
    $AveVn     = $AveVn/$nPts;
    $AveVe     = $AveVe/$nPts;

    # Now let's figure out the new pressure and temperature.

    $dz = $MaxHeight - $arlold;
    print "Max APRS Height : $MaxHeight (dz =  $dz)\n";
    $t = 273.0 + $ARLTemperature[$iARL];
    $h = $k * $t / ($m * $g);

    $Pressure = int($ARLPressure[$iARL] * exp(-$dz/$h) + 0.5);

#    print "Aves : $AveVn $AveVe $Pressure\n";

    push(@ARLPressure, $Pressure);
    push(@ARLHeight, $MaxHeight);
    push(@ARLTemperature, $ARLTemperature[$iARL]);
    push(@ARLDew, $ARLDew[$iARL]);
    push(@ARLVn, $AveVn);
    push(@ARLVe, $AveVe);

}

$outfile = $arl.".processed";
open(ARL,">$outfile");

if ($ARLLongitude > 0.0) {
    $ARLLongitude = $ARLLongitude - 360.0;
}

print ARL "$ARLLatitude $ARLLongitude $ARLElevationSave\n";
print ARL scalar(@ARLPressure),"\n";

$iARL = 0;
foreach $arlheight(@ARLHeight) {

    print ARL sprintf("%5d", $ARLPressure[$iARL]),".\t";
    print ARL sprintf("%6d", $ARLHeight[$iARL]),".\t";
    print ARL sprintf("%7.1f", $ARLTemperature[$iARL]),"\t";
    print ARL sprintf("%7.1f", $ARLDew[$iARL]),"\t";
    print ARL sprintf("%9.3f",$ARLVe[$iARL]),"\t";
    print ARL sprintf("%9.3f",$ARLVn[$iARL]),"\n";

    $iARL++;

}

#$CurrentElevation = $CurrentElevation/3.28;

if ($CurrentLongitude > 0.0) {
    $CurrentLongitude = $CurrentLongitude - 360.0;
}
print ARL "$CurrentLatitude $CurrentLongitude $CurrentElevation\n";
print ARL $DidBurst,"\n";

#force burst stuff; not sure what it is
$burstvar = 0;
if ($burstheight) {
    print ARL -$burstheight,"\n";
    $burstvar = 1;
} else {
    if ($bursttime) {
	print "Subtracting $dttotal from bursttime variable!\n";
	$bursttime = $bursttime-$dttotal;
	$bursttime = 0 if ($bursttime < 0);
	print ARL $bursttime,"\n";
	$burstvar = 1;
    }
}

if (!$burstvar) {
    print ARL "0\n";
}

if ($ARLLatitudeSave) {
    $n = scalar(@APRSLatitude)+1;
    print ARL $n,"\n";
    print ARL sprintf("%13.5f", $ARLLatitudeSave);
    if ($ARLLongitudeSave > 0.0) {
	$ARLLongitudeSave = $ARLLongitudeSave - 360.0;
    }
    print ARL sprintf("%13.5f", $ARLLongitudeSave),"\n";
} else {
    print ARL scalar(@APRSLatitude),"\n";
}

$iAPRS=0;
foreach $aprslatitude(@APRSLatitude) {
    print ARL sprintf("%13.5f", $APRSLatitude[$iAPRS]);
    if ($APRSLongitude[$iAPRS] > 0.0) {
	$APRSLongitude[$iAPRS] = $APRSLongitude[$iAPRS] - 360.0;
    }
    print ARL sprintf("%13.5f", $APRSLongitude[$iAPRS]),"\n";
    $iAPRS++;
}



close(ARL);

if ($ascent) {

    $command = "rm -f ARL.txt ; ln -s $arl.processed ARL.txt\n";
    print "-----> Running command:\n";
    print "  $command\n";
    system $command;

    open(INPUTS,">.ascent.$callsign");
    print INPUTS $payload."\n";
    print INPUTS $balloon."\n";
    print INPUTS $helium."\n";
    print INPUTS $parachute."\n";
    print INPUTS "4\n";
    $command = "./balloonModel3.exe < .ascent.$callsign";
    print "-----> Running command:\n";
    print "  $command\n";
    system $command;

}

if ($predict) {

    #$command = "rm -f ARL.txt ; ln -s $arl.processed ARL.txt\n";
    #print "-----> Running command:\n";
    #print "  $command\n";
    #system $command;

    open(INPUTS,">.predict.$callsign");
    print INPUTS $payload."\n";
    print INPUTS $balloon."\n";
    print INPUTS $helium."\n";
    print INPUTS $parachute."\n";
    print INPUTS "1\n";
    $command = "./run ".$outfile." < .predict.$callsign";
    print "-----> Running command:\n";
    print "  $command\n";
    system $command;

}

if ($clean) {
    $command = "rm -f $arl.processed .ascent.$callsign .predict.$callsign";
    print "-----> Running command:\n";
    print "  $command\n";
    system $command;
}


exit(1);


