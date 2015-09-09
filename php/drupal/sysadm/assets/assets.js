(function ($) {  
	Drupal.behaviors.assets = {
		attach: function(context, settings) {
			
			//删除资产[start]
			$('a.delete_assets_one').bind("click", function() {
			  	var url_object = this.href.split("/");
			  	var id = url_object[url_object.length-1];
			    if (confirm("你确定要删除吗？(删除后不可恢复)")) {
				    var AssetsDelete = function(data) {
				      if (data.result == true) {
				    	$('#delete_assets_loading_'+id).html('已完成');
				      }
				      else {
				    	$('#delete_assets_loading_'+id).html('失败');
				      }
			    	  window.location.href=window.location.href;
				    }
				    var loadingAssetsDelete = function(data) {
				      $('#delete_assets_loading_'+id).html('处理中...');
					}
				    $.ajax({
				      type: 'POST',
				      url: this.href, // Which url should be handle the ajax request. This is the url defined in the <a> html tag
				      beforeSend: loadingAssetsDelete,
				      success: AssetsDelete, // The js function that will be called upon success request
				      dataType: 'json', //define the type of data that is going to get back from the server
				      data: 'js=1' //Pass a key/value pair
				    });
				    return false;  // return false so the navigation stops here and not continue to the page in the link
				  }
				  else {
				  	return false;
				  }
			});
			
                        
                        //恢复资产[start]
			$('a.restory_assets_one').bind("click", function() {
			  	var url_object = this.href.split("/");
			  	var id = url_object[url_object.length-1];
			    if (confirm("你确定要还原吗？")) {
				    var AssetsRestory = function(data) {
				      if (data.result == true) {
				    	$('#restory_assets_loading_'+id).html('已还原');
				      }
				      else {
				    	$('#restory_assets_loading_'+id).html('失败');
				      }
                                    window.location.href=window.location.href;
				    }
				    var loadingAssetsRestory = function(data) {
				      $('#restory_assets_loading_'+id).html('处理中...');
					}
                                    alert(this.href);
                                    console.dir(this);
				    $.ajax({
				      type: 'POST',
				      url: this.href, // Which url should be handle the ajax request. This is the url defined in the <a> html tag
				      beforeSend: loadingAssetsRestory,
				      success: AssetsRestory, // The js function that will be called upon success request
                                      error: function(XMLHttpRequest, textStatus, errorThrown){  
        alert(XMLHttpRequest.readyState + XMLHttpRequest.status + XMLHttpRequest.responseText);  
                                      },
				      dataType: 'json', //define the type of data that is going to get back from the server
				      data: 'js=1' //Pass a key/value pair
				    });
				    return false;  // return false so the navigation stops here and not continue to the page in the link
				  }
				  else {
				  	return false;
				  }
			});
		}
	};
        
})(jQuery);

