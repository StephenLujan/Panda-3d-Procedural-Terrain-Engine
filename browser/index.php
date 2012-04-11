<head>

<script src="RunPanda3D.js" language="javascript"></script>

</head>
<body>
<style type="text/css">
	#myoutercontainer { position:relative center; width:973;
						margin-left: auto; margin-right: auto}

	embed
	{
		border-style:solid;
		border-color:#98bf21;
	}					
	
</style>
<div id="myoutercontainer">
			<script language="javascript">
				// Apparently it's recommended to leave 41 horizontal pixels for 
				// browser chrome assuming no vertical scroll bar will exist.
				// It's also recommended to leave 190 vertical pixels for OS
				// and browser bars. The lowest vertical resolution still
				// prevalent is probably 1280x720 aka HD. The lowest horizontal 
				// resolution still prevalent is probably 1024x768.
				// 1024-41 = 983   720-190 = 530
				// I'll drop an extra 10 pixels for a nice border and take 
				// 973 by 520 as a result. That's a nice wide 1.871 ratio.
				
				P3D_RunContent(
				'data', 'myapp.p3d',
				'id', 'Terrain',
				<?php 
				foreach ($_GET as $key => $val) {
					 echo "				'$key', '$val',\n"; 
				} 
				?>
				'width', '973', 'height', '520',
				'auto_start', '0',
				'onpythonload', 'OnPythonLoad()',
				'gameInfo', 'gameInfo',
				'noplugin_href', 'http://www.panda3d.org/download.php?runtime',
				'noplugin_img', 'noplugin.jpg'
				/*
				'splash_img', 'noplugin.jpg',
				'download_img', 'noplugin.jpg',
				'unauth_img', 'noplugin.jpg',
				'ready_img', 'noplugin.jpg',
				'launch_img', 'noplugin.jpg',
				'failed_img', 'noplugin.jpg',
				'bgcolor', '0,0,0'
				
				http://www.panda3d.org/manual/index.php/Splash_window_tags
				*/
				)
			</script>
</div>

</body>