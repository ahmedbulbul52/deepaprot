var filename='';
var resultFileName = '';
var resultFilePath ='';

function hideAllScreen() {
	$('#home_screen').hide();
	$('#upload_screen').hide();
	$('#model_run_screen').hide();
    $('#about_us_screen').hide();
}

function showScreen(divName) {
	$('#'+ divName).show();
}

$(document).ready(function() {  
    $('a').click(function(){
        var tabId = $(this).attr('id');
        var screenId= tabId.substr(3, tabId.length);
        if(tabId.substr(0,3)=='src'){
            hideAllScreen();
            showScreen(screenId);
            
           } 
    });
});

function disableScreen() {
    $('#srcmodel_run_screen').attr('disabled','disabled');
}

function uploadFile() {
    $('#loader-wrapper').show();
    console.log("in java script");
    var formdata, file, modeltype, acttype;
    formdata = new FormData();
    file = $('#fileSelect').get(0).files[0];
    formdata.append('dataset_file',file);
    console.log("the file: "+ formdata.get('dataset_file'));
    $.ajax({
        url:"/upload",
        type:"POST",
        data: formdata,
        processData: false,
        contentType: false,
        success: function(response){
            var obj = JSON.parse(response)
            if(obj.status=='OK'){
                $('#loader-wrapper').hide();
                filename = obj.file_name;
                console.log("file "+filename+ " has been uploaded successfully");
                $('#uploadText').hide();
                $('#smallText').hide();
                $('#file_div_1').hide();
                $('#file_div_2').hide();
                $('#uploadResponse').show();
                $('#uploadResponse').css('color', 'black');
                $('#uploadResponse').html("Congratulations! You have successfully uploaded the dataset file.");
                $('#goToMR').show();
            }
            else if(obj.status=='NOT CSV'){
                $('#loader-wrapper').hide();
                $('#uploadResponse').show();
                $('#uploadResponse').html("please upload a csv file!!!");
            }
            else{
                $('#loader-wrapper').hide();
                $('#uploadResponse').show();
                $('#uploadResponse').html("Oops!!! Dataset file not upoaded, some error has occured.");
            }
        },
 		error : function(){
                $('#loader-wrapper').hide();
                $('#uploadResponse').show();
                $('#uploadResponse').html("Oops!!! Dataset file not upoaded, some error has occured.");
				console.log("AJAX not working!");
	    }
    });
}

function runModel(){
    console.log("in java script");
    var formdata, modeltype, acttype;
    formdata = new FormData();

    if($('#modelType :selected').text()=='--select--' && $('#activationType :selected').text()=='--select--' ){
            $('#mod_error').show();
            $('#mod_error').html("* select a model type");
            $('#act_error').show();
            $('#act_error').html("* select an activation function");
            }

    else if($('#modelType :selected').text()=='--select--'){
        $('#act_error').hide();
        $('#mod_error').show();
        $('#mod_error').html("* select a model type");

    }
    else if($('#activationType :selected').text()=='--select--'){
        $('#mod_error').hide();
        $('#act_error').show();
        $('#act_error').html("* select an activation function");

    }
    else {
        $('#loader-wrapper').show();
        $('#mod_error').hide();
        $('#act_error').hide();
        modeltype = $('#modelType :selected').text();
        acttype = $('#activationType :selected').text();

        formdata.append('file_name', filename);
        formdata.append('model_type',modeltype);
        formdata.append('act_type', acttype);

        console.log("the file: "+ formdata.get('file_name'));
        console.log("the model: "+ formdata.get('model_type'));
        console.log("the activation: "+ formdata.get('act_type'));

       $.ajax({
            url:"/model",
            type:"POST",
            data: formdata,
            processData: false,
            contentType: false,
            success: function(response){
                var obj = JSON.parse(response)
                if(obj.status=='OK'){
                    $('#loader-wrapper').hide();
                    resultFileName= obj.result_filename;
                    resultFilePath = obj.result_file_path;
                    console.log(resultFilePath);
                    console.log(resultFileName);
                    console.log("result_file is: "+obj.result_filename);
                    $('#modActText').hide();
                    $('#mod_div_1').hide();
                    $('#mod_div_3').hide();
                    $('#mod_div_5').hide();
                    $('#uploadResponse2').show();
                    $('#uploadResponse2').css('color', 'black');
                    $('#uploadResponse2').html("The "+modeltype+" model with "+acttype+" activation successfully run on the "+filename+" dataset");
                    $('#mod_div_7').show();
                    $('#result_file_download_anch').attr("href","/download/"+resultFileName);
                }
                else if(obj.status=='NO FILE'){
                $('#loader-wrapper').hide();
                $('#uploadResponse2').show();
                $('#uploadResponse2').html("Oops!!!You haven't upload any data file, Please Upload a data from Upload Data screen");
            }
               else{
                    $('#loader-wrapper').hide();
                    $('#uploadResponse2').show();
                    $('#uploadResponse2').html("Oops!! some error occured");
                    console.log("Not success");
                }
        },
 		error : function(){
                $('#loader-wrapper').hide();
                $('#uploadResponse2').show();
                $('#uploadResponse2').html("Oops!! some error occured");
				console.log("AJAX not working!");
			}
    });
   }
}

hideAllScreen();
disableScreen();
showScreen('home_screen');
