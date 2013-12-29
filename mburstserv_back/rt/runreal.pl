#!/usr/bin/perl -s

$SIG{INT} = 'ctrlc';

    #my($callsign, $weight, $balloon, $parachute, $helium) = @_;

    $delay = 30 if (!$delay);

    $Done = 0;
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
    $year += 1900;
    $mon++;

    $counter = 1;

    $sMon="$mon";
    if ($mon < 10) 
    {
	$sMon = "0$sMon";
    }
    
    $sMday="$mday";
    if ($mday < 10)
    {
	$sMday = "0$sMday";
    }
    
    $dirName = $year."_".$sMon."_".$sMday;
    
    $command = "mkdir -p ".$dirName;
    print $command."\n";
    system $command;
        
    #$file = "index.html";
    
    #open(FILE, ">>$file") or die "Cant open $file: $!\n";
    #print FILE "<!DOCTYPE html>\n";
    #print FILE "<html>\n";
    #print FILE "\t<body>\n";
    #foreach $callsign(@callsigns)
    #{
#	print FILE "\t\t<a href=\"".$callsign.".html\">".$callsign."</a>\n";
    #}
    #print FILE "\t</body>\n";
    #print FILE "</html>\n";
    #close FILE;
    
    #$command = "scp index.html jasonx\@sftp.itcs.umich.edu:Public/html/";
    #print "uploading root file\n";
    #system $command;
    
    while( !$Done ) 
    {
	print "Handling ".$callsign."\n";
	    
	$aprsfile = "aprs_".$callsign."_".$year."_".$sMon."_".$sMday.".xml";
	
	$command = "perl driver.pl -payload=".$weight." -balloon=".$balloon." -parachute=".$parachute." -helium=".$helium." -predict -burstheight=11390 -callsign=".$callsign." -arl=ARL.txt -aprs=".$aprsfile;
	print $command."\n";
	system $command;
	
	$sCounter="$counter";
	if( $counter < 10 ) 
	{
	    $sCounter = "0$sCounter";
	}
	
	$command = "cp index.html ".$dirName."/".$callsign.$sCounter.".html";
	print "copying to dir\n";
	system $command;    
	
	$command = "mv index.html ".$callsign.".html";
	system $command;
	
	$command = "cp ".$callsign.".html ../../mburstserv_front/app/templates/";
	#$command = "scp ".$callsign.".html jasonx\@sftp.itcs.umich.edu:Public/html/";
	print "scp to afs\n";
	system $command;
	
	$command = "rm ".$callsign.".html";
	system $command;
	
	print "-----------------\n";
	
	
	$counter++;
	print "Loop end\n";
	print "-----------------\n";
	sleep(120);   
    }


sub ctrlc
{
    die "\nExiting";
}
