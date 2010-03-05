
(function($) {
	
$.fn.extend({

	wmd: function(){
		$.Wmd(this);
	}
});

$.Wmd = function (textarea){

	// The text that appears on the upper part of the dialog box when
	// entering links.
	var imageDialogText = "Enter the image URL.\n\nYou can also add a title, which will be displayed as a tool tip.\nExample:\nhttp://wmd-editor.com/images/cloud1.jpg   \"Optional title\"";
	var linkDialogText = "Enter the web address.\nYou can also add a title, which will be displayed as a tool tip.\nExample:\nhttp://wmd-editor.com/   \"Optional title\"";
	
	// The default text that appears in the dialog input box when entering
	// links.
	var imageDefaultText = "http://";
	var linkDefaultText = "http://";

    var global = {};
	// Used to work around some browser bugs where we can't use feature testing.
	global.isIE 		= $.browser.msie;
//	global.isIE_5or6 	= /msie 6/.test(nav.userAgent.toLowerCase()) || /msie 5/.test(nav.userAgent.toLowerCase());
	global.isOpera 		= $.browser.opera;
//	global.isKonqueror 	= /konqueror/.test(nav.userAgent.toLowerCase());



	// Some intervals in ms.  These can be adjusted to reduce the control's load.
	var pastePollInterval = 100;


    var output_type
    var $textarea = $(textarea);
    var $wmd = $textarea.parent();
    var $button_bar = $('<div class="wmd-button-bar"></div>');
    var $preview = $('<div class="wmd-preview"></div>');
    $textarea.addClass('wmd-input');
    var $editor = $('<div class="wmd-editor"/>');
    var $output;
   // var $output = $('<div class="wmd-output"/>');
  //  var $output = $('<textarea class="wmd-output"/>');
    $textarea.wrap($editor);
    $textarea.before($button_bar);
    $wmd.append($preview);
  //  $wmd.append($output);

    if ($output){
        output_type = $output[0].nodeName;
    }

    function init_wmd(){
        makeSpritedButtonRow();
        $button_bar.click(button_bar_click);
        $textarea.keydown(keydown_event);
        $textarea.keyup(keyup_event);
        if ($output){
            if (output_type == 'TEXTAREA'){
                $output.attr('readonly', 'readonly');
            }
        }
    }


    function getSelection(){

        if ('selectionStart' in $textarea[0]){
            /* dom 3 */
                var t = $textarea[0];
				var l = t.selectionEnd - t.selectionStart;
				return { start: t.selectionStart,
                         end: t.selectionEnd,
                         length: l,
                         text: t.value.substr(t.selectionStart, l) };
        }  else if (document.selection){
            // IE
                var t = $textarea[0];

				t.focus();

				var r = document.selection.createRange();
				if (r == null) {
					return { start: 0, end: t.value.length, length: 0 }
				}

				var re = t.createTextRange();
				var rc = re.duplicate();
				re.moveToBookmark(r.getBookmark());
				rc.setEndPoint('EndToStart', re);

				return { start: rc.text.length,
                         end: rc.text.length + r.text.length,
                         length: r.text.length,
                         text: r.text };
        } else {
            // no support
                var t = $textarea[0];

				return { start: 0, end: t.value.length, length: 0 };
            }
    }

    function keydown_event(e){

        if (e.ctrlKey || e.metaKey){

			var key = String.fromCharCode(e.keyCode).toLowerCase();
			switch(key) {
				case "b":
					do_action('bold');
					break;
				case "i":
					do_action('italic');
					break;
				case "l":
				    do_action('link');
					break;
				case "q":
					do_action('blockquote');
					break;
				case "k":
					do_action('code');
					break;
				case "g":
				    do_action('image');
					break;
				case "o":
					do_action('olist');
					break;
				case "u":
					do_action('ulist');
					break;
				case "h":
					do_action('heading');
					break;
				case "r":
					do_action('horizontal_rule');
					break;
				case "y":
					do_action('redo');
					break;
				case "z":
					if(e.shiftKey) {
					    do_action('redo');
					}
					else {
					    do_action('undo');
					}
					break;
				default:
                    console_log('key')
                    undoManager.handleModeChange(e);
					return e;
			}
            e.preventDefault();
            return false;
        } 
        undoManager.handleModeChange(e);
    }


    function keyup_event(e){
		// Auto-continue lists, code blocks and block quotes when
		// the enter key is pressed.
		if (!e.shiftKey && !e.ctrlKey && !e.metaKey && e.keyCode == 13) {
				do_action('autoindent');
		}
    }


    function make_button($button_row, button_class, button_title){
        var $button = $('<li class="wmd-button wmd-' + button_class + '-button" title="' + button_title + '">');
        // undo/redo buttons start disabled.
        if (button_class == 'undo' || button_class == 'redo'){
            $button.addClass('disabled');
        }
        $button_row.append($button);
    }

    function make_spacer($button_row, index){
        var spacer = '<li class="wmd-spacer wmd-spacer-' + index + '">'
        $button_row.append(spacer);
    }

	function makeSpritedButtonRow(){
	 	
        // create button holder
		var $button_row = $('<ul class="wmd-button-row">');
        $button_bar.append($button_row);
        // add buttons
        make_button($button_row, 'bold', "Strong <strong> Ctrl+B");
        make_button($button_row, 'italic', "Emphasis <em> Ctrl+I");
        make_spacer($button_row, 1);
        make_button($button_row, 'link', "Hyperlink <a> Ctrl+L");
        make_button($button_row, 'quote', "Blockquote <blockquote> Ctrl+Q");
        make_button($button_row, 'code', "Code Sample <pre><code> Ctrl+K");
        make_button($button_row, 'image', "Image <img> Ctrl+G");
        make_spacer($button_row, 2);
        make_button($button_row, 'olist', "Numbered List <ol> Ctrl+O");
        make_button($button_row, 'ulist', "Bulleted List <ul> Ctrl+U");
        make_button($button_row, 'heading', "Heading <h1>/<h2> Ctrl+H");
        make_button($button_row, 'hr', "Horizontal Rule <hr> Ctrl+R");
        make_spacer($button_row, 3);
        make_button($button_row, 'undo', "Undo - Ctrl+Z");
        make_button($button_row, 'redo', "Redo - Ctrl+Shift+Z");//Redo - Ctrl+Y
        make_button($button_row, 'help', "Help");

	}

    // hash of possible actions and the function to call.
    var actions = {
        bold : do_bold,
        italic : do_italic,
        link : do_link,
        image : do_image,
        quote : do_blockquote,
        code : do_code,
        olist : do_olist,
        ulist : do_ulist,
        heading : do_heading,
        hr : do_horizontal_rule,
        undo : do_undo,
        redo : do_redo,
        autoindent : do_autoindent
    
    };

    var useDefaultText = true; // FIXME why?
    var re = RegExp;
	var wmd  = Attacklab;

    // chunk is used for manipulating the text.
    var chunk = {};

    function get_selection(){
        var content = getSelection();
        chunk.start = content.start;
        chunk.end = content.end;
        chunk.selection = content.text;
        chunk.full = $textarea.val();
        chunk.before = chunk.full.substring(0, chunk.start);
        chunk.after = chunk.full.substring(chunk.end);
		chunk.startTag = "";
		chunk.endTag = "";
		chunk.scrollTop = $textarea.scrollTop();
    }


    function update_textarea(){
        chunk.before += chunk.startTag;
        chunk.after = chunk.endTag + chunk.after;
        $textarea.val(chunk.before + chunk.selection + chunk.after);
        $textarea.focus();
        var start = chunk.before.length;
        var end = start + chunk.selection.length;
        // FIXME have declared function for this
        if ('selectionStart' in $textarea[0]){
            $textarea[0].selectionStart = start;
            $textarea[0].selectionEnd = end;
        } else {
            alert('not implemented update_textarea()');
        }
		$textarea.scrollTop(chunk.scrollTop);
    }

    function button_bar_click(e){
        var $item = $(e.target);
        if ($item[0].nodeName == 'LI'){
            for (var action in actions){
                if ($item.hasClass('wmd-' + action + '-button')){
                    do_action(action);
                }
            }
        }
        return false;
    }

    function do_action(action){
				
        if (action == 'undo' || action == 'redo'){
            actions[action]();
        } else {
    		if (undoManager) {
	    		undoManager.setCommandMode();
		    }
            get_selection();
            actions[action]();
            update_textarea();
        }
        // update the preview
        previewManager.applyTimeout();
    }
    function get_prompt(imageDialogText, imageDefaultText){
        return prompt(imageDialogText);
    }

    function do_link(){
        do_LinkOrImage(false);
    }

    function do_image(){
        do_LinkOrImage(true);
    }

    function do_redo(){
        undoManager.redo();
    }

    function do_undo(){
        undoManager.undo();
    }

    function do_bold(){
		do_bold_or_italic(2, "strong text");
	}
	
	function do_italic(){
		do_bold_or_italic(1, "emphasized text");
    }

    function do_ulist(){
		do_list(false);
	}
	
	function do_olist(){
		do_list(true);
    }
	
	do_LinkOrImage = function(isImage){
	
		chunk.trimWhitespace();
		chunk.findTags(/\s*!?\[/, /\][ ]?(?:\n[ ]*)?(\[.*?\])?/);
		
		if (chunk.endTag.length > 1) {
		
			chunk.startTag = chunk.startTag.replace(/!?\[/, "");
			chunk.endTag = "";
			command.addLinkDef(chunk, null);
			
		}
		else {
		
			if (/\n\n/.test(chunk.selection)) {
				command.addLinkDef(chunk, null);
				return;
			}
			
			// The function to be executed when you enter a link and press OK or Cancel.
			// Marks up the link and adds the ref.
			var makeLinkMarkdown = function(link){
			
				if (link !== null) {
				
					chunk.startTag = chunk.endTag = "";
					var linkDef = " [999]: " + link;
					
					var num = command.addLinkDef(chunk, linkDef);
					chunk.startTag = isImage ? "![" : "[";
					chunk.endTag = "][" + num + "]";
					
					if (!chunk.selection) {
						if (isImage) {
							chunk.selection = "alt text";
						}
						else {
							chunk.selection = "link text";
						}
					}
				}
			};
			
			if (isImage) {
                var data = get_prompt(imageDialogText, imageDefaultText);
                makeLinkMarkdown(data);
			}
			else {
                var data = get_prompt(linkDialogText, linkDefaultText);
                makeLinkMarkdown(data);
			}
			return true;
		}
	};
	// nStars: 1 for italics, 2 for bold
	// insertText: If you just click the button without highlighting text, this gets inserted
	function do_bold_or_italic(nStars, insertText){
	
		// Get rid of whitespace and fixup newlines.
		chunk.trimWhitespace();
		chunk.selection = chunk.selection.replace(/\n{2,}/g, "\n");
		
		// Look for stars before and after.  Is the chunk already marked up?
		chunk.before.search(/(\**$)/);
		var starsBefore = re.$1;
		
		chunk.after.search(/(^\**)/);
		var starsAfter = re.$1;
		
		var prevStars = Math.min(starsBefore.length, starsAfter.length);
		
		// Remove stars if we have to since the button acts as a toggle.
		if ((prevStars >= nStars) && (prevStars != 2 || nStars != 1)) {
			chunk.before = chunk.before.replace(re("[*]{" + nStars + "}$", ""), "");
			chunk.after = chunk.after.replace(re("^[*]{" + nStars + "}", ""), "");
		}
		else if (!chunk.selection && starsAfter) {
			// It's not really clear why this code is necessary.  It just moves
			// some arbitrary stuff around.
			chunk.after = chunk.after.replace(/^([*_]*)/, "");
			chunk.before = chunk.before.replace(/(\s?)$/, "");
			var whitespace = re.$1;
			chunk.before = chunk.before + starsAfter + whitespace;
		}
		else {
		
			// In most cases, if you don't have any selected text and click the button
			// you'll get a selected, marked up region with the default text inserted.
			if (!chunk.selection && !starsAfter) {
				chunk.selection = insertText;
			}
			
			// Add the true markup.
			var markup = nStars <= 1 ? "*" : "**"; // shouldn't the test be = ?
			chunk.before = chunk.before + markup;
			chunk.after = markup + chunk.after;
		}
	};


	
	function do_blockquote(){
		
		chunk.selection = chunk.selection.replace(/^(\n*)([^\r]+?)(\n*)$/,
			function(totalMatch, newlinesBefore, text, newlinesAfter){
				chunk.before += newlinesBefore;
				chunk.after = newlinesAfter + chunk.after;
				return text;
			});
			
		chunk.before = chunk.before.replace(/(>[ \t]*)$/,
			function(totalMatch, blankLine){
				chunk.selection = blankLine + chunk.selection;
				return "";
			});
		
		var defaultText = useDefaultText ? "Blockquote" : "";
		chunk.selection = chunk.selection.replace(/^(\s|>)+$/ ,"");
		chunk.selection = chunk.selection || defaultText;
		
		if(chunk.before){
			chunk.before = chunk.before.replace(/\n?$/,"\n");
		}
		if(chunk.after){
			chunk.after = chunk.after.replace(/^\n?/,"\n");
		}
		
		chunk.before = chunk.before.replace(/(((\n|^)(\n[ \t]*)*>(.+\n)*.*)+(\n[ \t]*)*$)/,
			function(totalMatch){
				chunk.startTag = totalMatch;
				return "";
			});
			
		chunk.after = chunk.after.replace(/^(((\n|^)(\n[ \t]*)*>(.+\n)*.*)+(\n[ \t]*)*)/,
			function(totalMatch){
				chunk.endTag = totalMatch;
				return "";
			});
		
		var replaceBlanksInTags = function(useBracket){
			
			var replacement = useBracket ? "> " : "";
			
			if(chunk.startTag){
				chunk.startTag = chunk.startTag.replace(/\n((>|\s)*)\n$/,
					function(totalMatch, markdown){
						return "\n" + markdown.replace(/^[ ]{0,3}>?[ \t]*$/gm, replacement) + "\n";
					});
			}
			if(chunk.endTag){
				chunk.endTag = chunk.endTag.replace(/^\n((>|\s)*)\n/,
					function(totalMatch, markdown){
						return "\n" + markdown.replace(/^[ ]{0,3}>?[ \t]*$/gm, replacement) + "\n";
					});
			}
		};
		
		if(/^(?![ ]{0,3}>)/m.test(chunk.selection)){
			command.wrap(wmd.wmd_env.lineLength - 2);
			chunk.selection = chunk.selection.replace(/^/gm, "> ");
			replaceBlanksInTags(true);
			chunk.addBlankLines();
		}
		else{
			chunk.selection = chunk.selection.replace(/^[ ]{0,3}> ?/gm, "");
			command.unwrap();
			replaceBlanksInTags(false);
			
			if(!/^(\n|^)[ ]{0,3}>/.test(chunk.selection) && chunk.startTag){
				chunk.startTag = chunk.startTag.replace(/\n{0,2}$/, "\n\n");
			}
			
			if(!/(\n|^)[ ]{0,3}>.*$/.test(chunk.selection) && chunk.endTag){
				chunk.endTag=chunk.endTag.replace(/^\n{0,2}/, "\n\n");
			}
		}
		
		if(!/\n/.test(chunk.selection)){
			chunk.selection = chunk.selection.replace(/^(> *)/,
			function(wholeMatch, blanks){
				chunk.startTag += blanks;
				return "";
			});
		}
	};


	function do_code(){
		
		var hasTextBefore = /\S[ ]*$/.test(chunk.before);
		var hasTextAfter = /^[ ]*\S/.test(chunk.after);
		
		// Use 'four space' markdown if the selection is on its own
		// line or is multiline.
		if((!hasTextAfter && !hasTextBefore) || /\n/.test(chunk.selection)){
			
			chunk.before = chunk.before.replace(/[ ]{4}$/,
				function(totalMatch){
					chunk.selection = totalMatch + chunk.selection;
					return "";
				});
				
			var nLinesBefore = 1;
			var nLinesAfter = 1;
			
			
			if(/\n(\t|[ ]{4,}).*\n$/.test(chunk.before) || chunk.after === ""){
				nLinesBefore = 0; 
			}
			if(/^\n(\t|[ ]{4,})/.test(chunk.after)){
				nLinesAfter = 0; // This needs to happen on line 1
			}
			
			chunk.addBlankLines(nLinesBefore, nLinesAfter);
			
			if(!chunk.selection){
				chunk.startTag = "    ";
				chunk.selection = useDefaultText ? "enter code here" : "";
			}
			else {
				if(/^[ ]{0,3}\S/m.test(chunk.selection)){
					chunk.selection = chunk.selection.replace(/^/gm, "    ");
				}
				else{
					chunk.selection = chunk.selection.replace(/^[ ]{4}/gm, "");
				}
			}
		}
		else{
			// Use backticks (`) to delimit the code block.
			
			chunk.trimWhitespace();
			chunk.findTags(/`/, /`/);
			
			if(!chunk.startTag && !chunk.endTag){
				chunk.startTag = chunk.endTag="`";
				if(!chunk.selection){
					chunk.selection = useDefaultText ? "enter code here" : "";
				}
			}
			else if(chunk.endTag && !chunk.startTag){
				chunk.before += chunk.endTag;
				chunk.endTag = "";
			}
			else{
				chunk.startTag = chunk.endTag="";
			}
		}
	};
	
	function do_list(isNumberedList){
				
		// These are identical except at the very beginning and end.
		// Should probably use the regex extension function to make this clearer.
		var previousItemsRegex = /(\n|^)(([ ]{0,3}([*+-]|\d+[.])[ \t]+.*)(\n.+|\n{2,}([*+-].*|\d+[.])[ \t]+.*|\n{2,}[ \t]+\S.*)*)\n*$/;
		var nextItemsRegex = /^\n*(([ ]{0,3}([*+-]|\d+[.])[ \t]+.*)(\n.+|\n{2,}([*+-].*|\d+[.])[ \t]+.*|\n{2,}[ \t]+\S.*)*)\n*/;
		
		// The default bullet is a dash but others are possible.
		// This has nothing to do with the particular HTML bullet,
		// it's just a markdown bullet.
		var bullet = "-";
		
		// The number in a numbered list.
		var num = 1;
		
		// Get the item prefix - e.g. " 1. " for a numbered list, " - " for a bulleted list.
		var getItemPrefix = function(){
			var prefix;
			if(isNumberedList){
				prefix = " " + num + ". ";
				num++;
			}
			else{
				prefix = " " + bullet + " ";
			}
			return prefix;
		};
		
		// Fixes the prefixes of the other list items.
		var getPrefixedItem = function(itemText){
		
			// The numbering flag is unset when called by autoindent.
			if(isNumberedList === undefined){
				isNumberedList = /^\s*\d/.test(itemText);
			}
			
			// Renumber/bullet the list element.
			itemText = itemText.replace(/^[ ]{0,3}([*+-]|\d+[.])\s/gm,
				function( _ ){
					return getItemPrefix();
				});
				
			return itemText;
		};
		
		chunk.findTags(/(\n|^)*[ ]{0,3}([*+-]|\d+[.])\s+/, null);
		
		if(chunk.before && !/\n$/.test(chunk.before) && !/^\n/.test(chunk.startTag)){
			chunk.before += chunk.startTag;
			chunk.startTag = "";
		}
		
		if(chunk.startTag){
			
			var hasDigits = /\d+[.]/.test(chunk.startTag);
			chunk.startTag = "";
			chunk.selection = chunk.selection.replace(/\n[ ]{4}/g, "\n");
			command.unwrap(chunk);
			chunk.addBlankLines();
			
			if(hasDigits){
				// Have to renumber the bullet points if this is a numbered list.
				chunk.after = chunk.after.replace(nextItemsRegex, getPrefixedItem);
			}
			if(isNumberedList == hasDigits){
				return;
			}
		}
		
		var nLinesBefore = 1;
		
		chunk.before = chunk.before.replace(previousItemsRegex,
			function(itemText){
				if(/^\s*([*+-])/.test(itemText)){
					bullet = re.$1;
				}
				nLinesBefore = /[^\n]\n\n[^\n]/.test(itemText) ? 1 : 0;
				return getPrefixedItem(itemText);
			});
			
		if(!chunk.selection){
			chunk.selection = useDefaultText ? "List item" : " ";
		}
		
		var prefix = getItemPrefix();
		
		var nLinesAfter = 1;
		
		chunk.after = chunk.after.replace(nextItemsRegex,
			function(itemText){
				nLinesAfter = /[^\n]\n\n[^\n]/.test(itemText) ? 1 : 0;
				return getPrefixedItem(itemText);
			});
			
		chunk.trimWhitespace(true);
		chunk.addBlankLines(nLinesBefore, nLinesAfter, true);
		chunk.startTag = prefix;
		var spaces = prefix.replace(/./g, " ");
		command.wrap(chunk, wmd.wmd_env.lineLength - spaces.length);
		chunk.selection = chunk.selection.replace(/\n/g, "\n" + spaces);
	};
	
	function do_heading(){
		
		// Remove leading/trailing whitespace and reduce internal spaces to single spaces.
		chunk.selection = chunk.selection.replace(/\s+/g, " ");
		chunk.selection = chunk.selection.replace(/(^\s+|\s+$)/g, "");
		
		// If we clicked the button with no selected text, we just
		// make a level 2 hash header around some default text.
		if(!chunk.selection){
			chunk.startTag = "## ";
			chunk.selection = "Heading";
			chunk.endTag = " ##";
			return;
		}
		
		var headerLevel = 0;		// The existing header level of the selected text.
		
		// Remove any existing hash heading markdown and save the header level.
		chunk.findTags(/#+[ ]*/, /[ ]*#+/);
		if(/#+/.test(chunk.startTag)){
			headerLevel = re.lastMatch.length;
		}
		chunk.startTag = chunk.endTag = "";
		
		// Try to get the current header level by looking for - and = in the line
		// below the selection.
		chunk.findTags(null, /\s?(-+|=+)/);
		if(/=+/.test(chunk.endTag)){
			headerLevel = 1;
		}
		if(/-+/.test(chunk.endTag)){
			headerLevel = 2;
		}
		
		// Skip to the next line so we can create the header markdown.
		chunk.startTag = chunk.endTag = "";
		chunk.addBlankLines(1, 1);

		// We make a level 2 header if there is no current header.
		// If there is a header level, we substract one from the header level.
		// If it's already a level 1 header, it's removed.
		var headerLevelToCreate = headerLevel == 0 ? 2 : headerLevel - 1;
		
		if(headerLevelToCreate > 0){
			
			// The button only creates level 1 and 2 underline headers.
			// Why not have it iterate over hash header levels?  Wouldn't that be easier and cleaner?
			var headerChar = headerLevelToCreate >= 2 ? "-" : "=";
			var len = chunk.selection.length;
			if(len > wmd.wmd_env.lineLength){
				len = wmd.wmd_env.lineLength;
			}
			chunk.endTag = "\n";
			while(len--){
				chunk.endTag += headerChar;
			}
		}
	}
	
	function do_horizontal_rule(){
		chunk.startTag = "----------\n";
		chunk.selection = "";
		chunk.addBlankLines(2, 1, true);
	}



	// If remove is false, the whitespace is transferred
	// to the before/after regions.
	//
	// If remove is true, the whitespace disappears.
	chunk.trimWhitespace = function(remove){
	
		this.selection = this.selection.replace(/^(\s*)/, "");
		
		if (!remove) {
			this.before += re.$1;
		}
		
		this.selection = this.selection.replace(/(\s*)$/, "");
		
		if (!remove) {
			this.after = re.$1 + this.after;
		}
	};


	
	chunk.addBlankLines = function(nLinesBefore, nLinesAfter, findExtraNewlines){
	
		if (nLinesBefore === undefined) {
			nLinesBefore = 1;
		}
		
		if (nLinesAfter === undefined) {
			nLinesAfter = 1;
		}
		
		nLinesBefore++;
		nLinesAfter++;
		
		var regexText;
		var replacementText;
		
		this.selection = this.selection.replace(/(^\n*)/, "");
		this.startTag = this.startTag + re.$1;
		this.selection = this.selection.replace(/(\n*$)/, "");
		this.endTag = this.endTag + re.$1;
		this.startTag = this.startTag.replace(/(^\n*)/, "");
		this.before = this.before + re.$1;
		this.endTag = this.endTag.replace(/(\n*$)/, "");
		this.after = this.after + re.$1;
		
		if (this.before) {
		
			regexText = replacementText = "";
			
			while (nLinesBefore--) {
				regexText += "\\n?";
				replacementText += "\n";
			}
			
			if (findExtraNewlines) {
				regexText = "\\n*";
			}
			this.before = this.before.replace(new re(regexText + "$", ""), replacementText);
		}
		
		if (this.after) {
		
			regexText = replacementText = "";
			
			while (nLinesAfter--) {
				regexText += "\\n?";
				replacementText += "\n";
			}
			if (findExtraNewlines) {
				regexText = "\\n*";
			}
			
			this.after = this.after.replace(new re(regexText, ""), replacementText);
		}
	};
	
	
	// startRegex: a regular expression to find the start tag
	// endRegex: a regular expresssion to find the end tag
	chunk.findTags = function(startRegex, endRegex){
	
		var chunkObj = this;
		var regex;
		
		if (startRegex) {
			
			regex = util.extendRegExp(startRegex, "", "$");
			
			this.before = this.before.replace(regex, 
				function(match){
					chunkObj.startTag = chunkObj.startTag + match;
					return "";
				});
			
			regex = util.extendRegExp(startRegex, "^", "");
			
			this.selection = this.selection.replace(regex, 
				function(match){
					chunkObj.startTag = chunkObj.startTag + match;
					return "";
				});
		}
		
		if (endRegex) {
			
			regex = util.extendRegExp(endRegex, "", "$");
			
			this.selection = this.selection.replace(regex,
				function(match){
					chunkObj.endTag = match + chunkObj.endTag;
					return "";
				});

			regex = util.extendRegExp(endRegex, "^", "");
			
			this.after = this.after.replace(regex,
				function(match){
					chunkObj.endTag = match + chunkObj.endTag;
					return "";
				});
		}
	};
	

    var command = {};

	// The markdown symbols - 4 spaces = code, > = blockquote, etc.
	command.prefixes = "(?:\\s{4,}|\\s*>|\\s*-\\s+|\\s*\\d+\\.|=|\\+|-|_|\\*|#|\\s*\\[[^\n]]+\\]:)";
	
	// Remove markdown symbols from the chunk selection.
	command.unwrap = function(){
		var txt = new re("([^\\n])\\n(?!(\\n|" + command.prefixes + "))", "g");
		chunk.selection = chunk.selection.replace(txt, "$1 $2");
	};
	
	command.wrap = function(len){
		command.unwrap();
		var regex = new re("(.{1," + len + "})( +|$\\n?)", "gm");
		
		chunk.selection = chunk.selection.replace(regex, function(line, marked){
			if (new re("^" + command.prefixes, "").test(line)) {
				return line;
			}
			return marked + "\n";
		});
		
		chunk.selection = chunk.selection.replace(/\s+$/, "");
	};



	command.stripLinkDefs = function(text, defsToAdd){
	
		text = text.replace(/^[ ]{0,3}\[(\d+)\]:[ \t]*\n?[ \t]*<?(\S+?)>?[ \t]*\n?[ \t]*(?:(\n*)["(](.+?)[")][ \t]*)?(?:\n+|$)/gm, 
			function(totalMatch, id, link, newlines, title){	
				defsToAdd[id] = totalMatch.replace(/\s*$/, "");
				if (newlines) {
					// Strip the title and return that separately.
					defsToAdd[id] = totalMatch.replace(/["(](.+?)[")]$/, "");
					return newlines + title;
				}
				return "";
			});
		
		return text;
	};
	
	command.addLinkDef = function(chunk, linkDef){
	
		var refNumber = 0; // The current reference number
		var defsToAdd = {}; //
		// Start with a clean slate by removing all previous link definitions.
		chunk.before = command.stripLinkDefs(chunk.before, defsToAdd);
		chunk.selection = command.stripLinkDefs(chunk.selection, defsToAdd);
		chunk.after = command.stripLinkDefs(chunk.after, defsToAdd);
		
		var defs = "";
		var regex = /(\[(?:\[[^\]]*\]|[^\[\]])*\][ ]?(?:\n[ ]*)?\[)(\d+)(\])/g;
		
		var addDefNumber = function(def){
			refNumber++;
			def = def.replace(/^[ ]{0,3}\[(\d+)\]:/, "  [" + refNumber + "]:");
			defs += "\n" + def;
		};
		
		var getLink = function(wholeMatch, link, id, end){
		
			if (defsToAdd[id]) {
				addDefNumber(defsToAdd[id]);
				return link + refNumber + end;
				
			}
			return wholeMatch;
		};
		
		chunk.before = chunk.before.replace(regex, getLink);
		
		if (linkDef) {
			addDefNumber(linkDef);
		}
		else {
			chunk.selection = chunk.selection.replace(regex, getLink);
		}
		
		var refOut = refNumber;
		
		chunk.after = chunk.after.replace(regex, getLink);
		
		if (chunk.after) {
			chunk.after = chunk.after.replace(/\n*$/, "");
		}
		if (!chunk.after) {
			chunk.selection = chunk.selection.replace(/\n*$/, "");
		}
		
		chunk.after += "\n\n" + defs;
		
		return refOut;
	};

	// Moves the cursor to the next line and continues lists, quotes and code.
	function do_autoindent(){
		
		chunk.before = chunk.before.replace(/(\n|^)[ ]{0,3}([*+-]|\d+[.])[ \t]*\n$/, "\n\n");
		chunk.before = chunk.before.replace(/(\n|^)[ ]{0,3}>[ \t]*\n$/, "\n\n");
		chunk.before = chunk.before.replace(/(\n|^)[ \t]+\n$/, "\n\n");
		
		useDefaultText = false;
		
		if(/(\n|^)[ ]{0,3}([*+-])[ \t]+.*\n$/.test(chunk.before)){
			if(do_ulist){
				do_ulist();
			}
		}
		if(/(\n|^)[ ]{0,3}(\d+[.])[ \t]+.*\n$/.test(chunk.before)){
			if(do_olist){
				do_olist();
			}
		}
		if(/(\n|^)[ ]{0,3}>[ \t]+.*\n$/.test(chunk.before)){
			if(do_blockquote){
				do_blockquote();
			}
		}
		if(/(\n|^)(\t|[ ]{4,}).*\n$/.test(chunk.before)){
			if(do_code){
				do_code();
			}
		}
	};


    var util = {};

	// Extends a regular expression.  Returns a new RegExp
	// using pre + regex + post as the expression.
	// Used in a few functions where we have a base
	// expression and we want to pre- or append some
	// conditions to it (e.g. adding "$" to the end).
	// The flags are unchanged.
	//
	// regex is a RegExp, pre and post are strings.
	util.extendRegExp = function(regex, pre, post){
		
		if (pre === null || pre === undefined)
		{
			pre = "";
		}
		if(post === null || post === undefined)
		{
			post = "";
		}
		
		var pattern = regex.toString();
		var flags = "";
		
		// Replace the flags with empty space and store them.
		// Technically, this can match incorrect flags like "gmm".
		var result = pattern.match(/\/([gim]*)$/);
		if (result === null) {
			flags = result[0];
		}
		else {
			flags = "";
		}
		
		// Remove the flags and slash delimiters from the regular expression.
		pattern = pattern.replace(/(^\/|\/[gim]*$)/g, "");
		pattern = pre + pattern + post;
		
		return new RegExp(pattern, flags);
	}

    util.isVisible = function(){
        // check textarea is visible and in the DOM
        return ($textarea.css('display') != 'none' && $textarea.parents('body').size());
    }

	// Converts \r\n and \r to \n.
	util.fixEolChars = function(text){
		text = text.replace(/\r\n/g, "\n");
		text = text.replace(/\r/g, "\n");
		return text;
	};
	
	// The input textarea state/contents.
	// This is used to implement undo/redo by the undo manager.
	var TextareaState = function(){
	
		// Aliases
		var stateObj = this;
		var inputArea = $textarea;
		
		this.init = function() {
		
			if (!util.isVisible()) {
				return;
			}

			this.setInputAreaSelectionStartEnd();
			this.scrollTop = $textarea.scrollTop();
            var selectionStart = getSelection().start;
			if (!this.text && selectionStart || selectionStart === 0) {
				this.text = $textarea.val();
			}
		}
		
		// Sets the selected text in the input box after we've performed an
		// operation.
		this.setInputAreaSelection = function(){
		
			if (!util.isVisible()) {
				return;
			}
			
            var selectionStart = getSelection().start;
			if (selectionStart !== undefined){ // && !global.isOpera) {
			
				$textarea.focus();
                // FIXME make function call
				inputArea[0].selectionStart = stateObj.start;
				inputArea[0].selectionEnd = stateObj.end;
				$textarea.scrollTop(stateObj.scrollTop);
			}
/*			else if (doc.selection) {
				
				if (doc.activeElement && doc.activeElement !== inputArea) {
					return;
				}
					
				inputArea.focus();
				var range = inputArea.createTextRange();
				range.moveStart("character", -inputArea.value.length);
				range.moveEnd("character", -inputArea.value.length);
				range.moveEnd("character", stateObj.end);
				range.moveStart("character", stateObj.start);
				range.select();
			}  */
		};
		
		this.setInputAreaSelectionStartEnd = function(){
	        var selection = getSelection();
		    if (selection.start || selection.start === 0) {
			
				stateObj.start = selection.start;
				stateObj.end = selection.end;
			}
	/*		else if (doc.selection) {
				
				stateObj.text = util.fixEolChars(inputArea.value);
				
				// IE loses the selection in the textarea when buttons are
				// clicked.  On IE we cache the selection and set a flag
				// which we check for here.
				var range;
				if(wmd.ieRetardedClick && wmd.ieCachedRange) {
					range = wmd.ieCachedRange;
					wmd.ieRetardedClick = false;
				}
				else {
					range = doc.selection.createRange();
				}

				var fixedRange = util.fixEolChars(range.text);
				var marker = "\x07";
				var markedRange = marker + fixedRange + marker;
				range.text = markedRange;
				var inputText = util.fixEolChars(inputArea.value);
					
				range.moveStart("character", -markedRange.length);
				range.text = fixedRange;

				stateObj.start = inputText.indexOf(marker);
				stateObj.end = inputText.lastIndexOf(marker) - marker.length;
					
				var len = stateObj.text.length - util.fixEolChars(inputArea.value).length;
					
				if (len) {
					range.moveStart("character", -fixedRange.length);
					while (len--) {
						fixedRange += "\n";
						stateObj.end += 1;
					}
					range.text = fixedRange;
				}
					
				this.setInputAreaSelection();
			}*/
		};
		
		// Restore this state into the input area.
		this.restore = function(){
			if (stateObj.text != undefined && stateObj.text != $textarea.val()) {
				$textarea.val(stateObj.text);
			}
			this.setInputAreaSelection();
			$textarea.scrollTop(stateObj.scrollTop);
		};
		
		// Gets a collection of HTML chunks from the inptut textarea.
		this.getChunks = function(){
		
			var chunk = {};
			
			chunk.before = util.fixEolChars(stateObj.text.substring(0, stateObj.start));
			chunk.startTag = "";
			chunk.selection = util.fixEolChars(stateObj.text.substring(stateObj.start, stateObj.end));
			chunk.endTag = "";
			chunk.after = util.fixEolChars(stateObj.text.substring(stateObj.end));
			chunk.scrollTop = stateObj.scrollTop;
			
			return chunk;
		};
		
		// Sets the TextareaState properties given a chunk of markdown.
		this.setChunks = function(chunk){
		
			chunk.before = chunk.before + chunk.startTag;
			chunk.after = chunk.endTag + chunk.after;
			
			if (global.isOpera) {
				chunk.before = chunk.before.replace(/\n/g, "\r\n");
				chunk.selection = chunk.selection.replace(/\n/g, "\r\n");
				chunk.after = chunk.after.replace(/\n/g, "\r\n");
			}
			
			this.start = chunk.before.length;
			this.end = chunk.before.length + chunk.selection.length;
			this.text = chunk.before + chunk.selection + chunk.after;
			this.scrollTop = chunk.scrollTop;
		};

		this.init();
	};

/*
Don't think this is needed anymore
	
	
	// Watches the input textarea, polling at an interval and runs
	// a callback function if anything has changed.
	var inputPoller = function(callback, interval){
	
		var pollerObj = this;
		
		// Stored start, end and text.  Used to see if there are changes to the input.
		var lastStart;
		var lastEnd;
		var markdown;
		
		var killHandle; // Used to cancel monitoring on destruction.
		// Checks to see if anything has changed in the textarea.
		// If so, it runs the callback.
		this.tick = function(){
		
			if (!util.isVisible()) {
				return;
			}
			
			// Update the selection start and end, text.
            var selection = $textarea.getSelection();
			if (selection.start || selection.start === 0) {
				var start = selection.start;
				var end = selection.end;
				if (start != lastStart || end != lastEnd) {
					lastStart = start;
					lastEnd = end;
					
					if (markdown != $textarea.val()) {
						markdown = $textarea.val();
						return true;
					}
				}
			}
			return false;
		};
		
		
		var doTickCallback = function(){
		
			if (!util.isVisible()) {
				return;
			}
			
			// If anything has changed, call the function.
			if (pollerObj.tick()) {
				callback();
			}
		};
		
		// Set how often we poll the textarea for changes.
		var assignInterval = function(){
			// previewPollInterval is set at the top of the namespace.
			killHandle = setInterval(doTickCallback, interval);
		};
		
		this.destroy = function(){
			clearInterval(killHandle);
		};
		
		assignInterval();
	};
*/
	// Handles pushing and popping TextareaStates for undo/redo commands.
	// I should rename the stack variables to list.
	var undoManager = function (callback){
	
		var undoObj = this;
		var undoStack = []; // A stack of undo states
		var stackPtr = 0; // The index of the current state
		var mode = "none";
		var lastState; // The last state
		var poller;
		var timer; // The setTimeout handle for cancelling the timer
		var inputStateObj;
		
		// Set the mode for later logic steps.
		function setMode(newMode, noSave){
		
			if (mode != newMode) {
				mode = newMode;
				if (!noSave) {
					saveState();
				}
			}
			
			if (!global.isIE || mode != "moving") {
				timer = setTimeout(refreshState, 1);
			}
			else {
				inputStateObj = null;
			}
		}
		
		function refreshState(){
			inputStateObj = new TextareaState();
            if (poller){
			    poller.tick();
            }
			timer = undefined;
            update_button_state();
            if (previewManager){
                previewManager.applyTimeout();
            }
		}
		
		function setCommandMode(){
			mode = "command";
			saveState();
			timer = setTimeout(refreshState, 0);
		}
		
		function canUndo(){
			return stackPtr > 1;
		}
		
		function canRedo(){
			if (undoStack[stackPtr + 1]) {
				return true;
			}
			return false;
		}
		
		// Removes the last state and restores it.
		function undo(){
			if (canUndo()) {
				if (lastState) {
					// What about setting state -1 to null or checking for undefined?
					lastState.restore();
					lastState = null;
				}
				else {
					undoStack[stackPtr] = new TextareaState();
					undoStack[--stackPtr].restore();
					
					if (callback) {
						callback();
					}
				}
			}
			
			mode = "none";
			$textarea.focus();
			refreshState();
		}
		
		// Redo an action.
		function redo(){
		
			if (canRedo()) {
			
				undoStack[++stackPtr].restore();
				
				if (callback) {
					callback();
				}
			}
			
			mode = "none";
			$textarea.focus();
			refreshState();
		}
		
		// Push the input area state to the stack.
		var saveState = function(){
		
			var currState = inputStateObj || new TextareaState();
			
			if (!currState) {
				return false;
			}
			if (mode == "moving") {
				if (!lastState) {
					lastState = currState;
				}
				return;
			}
			if (lastState) {
				if (undoStack[stackPtr - 1].text != lastState.text) {
					undoStack[stackPtr++] = lastState;
				}
				lastState = null;
			}
			undoStack[stackPtr++] = currState;
			undoStack[stackPtr + 1] = null;
			if (callback) {
				callback();
			}
		}

        function update_button_state(){
            // update the button
            if (canRedo()){
                $button_bar.find('li.wmd-redo-button').removeClass('disabled');
            } else {
                $button_bar.find('li.wmd-redo-button').addClass('disabled');
            }
            if (canUndo()){
                $button_bar.find('li.wmd-undo-button').removeClass('disabled');
            } else {
                $button_bar.find('li.wmd-undo-button').addClass('disabled');
            }
        }

		// Set the mode depending on what is going on in the input area.
		var handleModeChange = function(e){
		
			if (!e.ctrlKey && !e.metaKey) {
			
				var keyCode = e.keyCode;
				
				if ((keyCode >= 33 && keyCode <= 40) || (keyCode >= 63232 && keyCode <= 63235)) {
					// 33 - 40: page up/dn and arrow keys
					// 63232 - 63235: page up/dn and arrow keys on safari
					setMode("moving");
				}
				else if (keyCode == 8 || keyCode == 46 || keyCode == 127) {
					// 8: backspace
					// 46: delete
					// 127: delete
					setMode("deleting");
				}
				else if (keyCode == 13) {
					// 13: Enter
					setMode("newlines");
				}
				else if (keyCode == 27) {
					// 27: escape
					setMode("escape");
				}
				else if ((keyCode < 16 || keyCode > 20) && keyCode != 91) {
					// 16-20 are shift, etc. 
					// 91: left window key
					// I think this might be a little messed up since there are
					// a lot of nonprinting keys above 20.
					setMode("typing");
				}
			}
            
		};
		
			var handlePaste = function(){
				if (global.isIE || (inputStateObj && inputStateObj.text != $textarea.val())) {
					if (timer == undefined) {
						mode = "paste";
						saveState();
						refreshState();
					}
				}
		};
		
		var init = function(){
          //  $textarea.keydown(handleModeChange);
            $textarea.mousedown(function (){setMode("moving");});
			$textarea.bind('paste', handlePaste);
			$textarea.bind('drop', handlePaste);
			$textarea.bind('cut', handlePaste);

            // FIXME this seems to just be covering up for problems elsewhere
			// pastePollInterval is specified at the beginning of this namespace.
//			poller = new inputPoller(handlePaste, pastePollInterval);
			
			refreshState();
			saveState();
		};
		
		this.destroy = function(){
			if (poller) {
				poller.destroy();
			}
		};
		
		init();
        return {
            undo : function (){undo();},
            redo : function (){redo();},
            setCommandMode : function (){setCommandMode();},
            handleModeChange : function (e){handleModeChange(e);}
        }
	}();


	
	var previewManager = function(){
		
		var managerObj = this;
		var converter;
		var poller;
		var timeout;
		var elapsedTime;
		var oldInputText;
		var htmlOut;
		var maxDelay = 3000;
		var startType = "delayed"; // The other legal value is "manual"
		
		
		var getDocScrollTop = function(){
		
			var result = 0;
			
			if (top.innerHeight) {
				result = top.pageYOffset;
			}
			else 
				if (doc.documentElement && doc.documentElement.scrollTop) {
					result = doc.documentElement.scrollTop;
				}
				else 
					if (doc.body) {
						result = doc.body.scrollTop;
					}
			
			return result;
		};
		
		var makePreviewHtml = function(){
	
			// If there are no registered preview and output panels
			// there is nothing to do.
			if (!$preview && !$output) {
				return;
			}
			var text = $textarea.val();
			if (text && text == oldInputText) {
				return; // Input text hasn't changed.
			}
			else {
				oldInputText = text;
			}
			
			var prevTime = new Date().getTime();
			
			if (!converter && Showdown) {
				converter = new Showdown.converter();
			}
			
			if (converter) {
				text = converter.makeHtml(text);
			}
			
			// Calculate the processing time of the HTML creation.
			// It's used as the delay time in the event listener.
			var currTime = new Date().getTime();
			elapsedTime = currTime - prevTime;
			
			pushPreviewHtml(text);
			htmlOut = text;
		};
		
		// setTimeout is already used.  Used as an event listener.
		var applyTimeout = function(){
		
			if (timeout) {
				clearTimeout(timeout);
				timeout = undefined;
			}
			
			if (startType !== "manual") {
			
				var delay = 0;
				
				if (startType === "delayed") {
					delay = elapsedTime;
				}
				
				if (delay > maxDelay) {
					delay = maxDelay;
				}
				timeout = setTimeout(makePreviewHtml, delay);
			}
		};
		/*
		var getScaleFactor = function(panel){
			if (panel.scrollHeight <= panel.clientHeight) {
				return 1;
			}
			return panel.scrollTop / (panel.scrollHeight - panel.clientHeight);
		};
		*/
/*		var setPanelScrollTops = function(){
		
			if (wmd.panels.preview) {
				wmd.panels.preview.scrollTop = (wmd.panels.preview.scrollHeight - wmd.panels.preview.clientHeight) * getScaleFactor(wmd.panels.preview);
				;
			}
			
			if (wmd.panels.output) {
				wmd.panels.output.scrollTop = (wmd.panels.output.scrollHeight - wmd.panels.output.clientHeight) * getScaleFactor(wmd.panels.output);
				;
			}
		};
*/		
		this.refresh = function(requiresRefresh){
		
			if (requiresRefresh) {
				oldInputText = "";
				makePreviewHtml();
			}
			else {
				applyTimeout();
			}
		};
		
		this.processingTime = function(){
			return elapsedTime;
		};
		
		// The output HTML
		this.output = function(){
			return htmlOut;
		};
		
		// The mode can be "manual" or "delayed"
		this.setUpdateMode = function(mode){
			startType = mode;
			managerObj.refresh();
		};
		
		var isFirstTimeFilled = true;
		
		var pushPreviewHtml = function(text){
		
	//		var emptyTop = position.getTop(wmd.panels.input) - getDocScrollTop();
			
			// Send the encoded HTML to the output textarea/div.
			if ($output) {
				// The value property is only defined if the output is a textarea.
				if (output_type == 'TEXTAREA') {
					$output.val(text);
				}
				// Otherwise we are just replacing the text in a div.
				// Send the HTML wrapped in <pre><code>
				else {
					var newText = text.replace(/&/g, "&amp;");
					newText = newText.replace(/</g, "&lt;");
					$output.html("<pre><code>" + newText + "</code></pre>");
				}
			}
			
			if ($preview) {
				$preview.html(text);
			}
			
			//setPanelScrollTops();
			
			if (isFirstTimeFilled) {
				isFirstTimeFilled = false;
				return;
			}
			/*
			var fullTop = position.getTop(wmd.panels.input) - getDocScrollTop();
			
			if (global.isIE) {
				top.setTimeout(function(){
					top.scrollBy(0, fullTop - emptyTop);
				}, 0);
			}
			else {
				top.scrollBy(0, fullTop - emptyTop);
			} */
		};
		
		var init = function(){
		
			makePreviewHtml();
			
			if ($preview) {
				$preview.scrollTop(0);
			}
			if ($output) {
				$output.scrollTop(0);
			}
		};
		
		this.destroy = function(){
			if (poller) {
				poller.destroy();
			}
		};
		
		init();
        return {
            applyTimeout : function (){applyTimeout();}
        }
	}();

    init_wmd();
};

})(jQuery);


var Attacklab = Attacklab || {};

/// KEEP THIS
Attacklab.wmd_env = {};
Attacklab.account_options = {};
Attacklab.wmd_defaults = {version:1, output:"HTML", lineLength:40, delayLoad:false};

if(!Attacklab.wmd)
{
	Attacklab.wmd = function()
	{
		Attacklab.loadEnv = function()
		{
			var mergeEnv = function(env)
			{
				if(!env)
				{
					return;
				}
			
				for(var key in env)
				{
					Attacklab.wmd_env[key] = env[key];
				}
			};
			
			mergeEnv(Attacklab.wmd_defaults);
			mergeEnv(Attacklab.account_options);
			mergeEnv(top["wmd_options"]);
			Attacklab.full = true;
			
			var defaultButtons = "bold italic link blockquote code image ol ul heading hr";
			Attacklab.wmd_env.buttons = Attacklab.wmd_env.buttons || defaultButtons;
		};
		Attacklab.loadEnv();

	};
	
	Attacklab.wmd();
	//Attacklab.wmdBase();
	//Attacklab.Util.startEditor();
};

