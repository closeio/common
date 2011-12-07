function reload() {
    location.href=location.protocol+'//'+location.host+location.pathname+location.search;
}

function htmlescape(text) {
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function linebreaksbr(text) {
    return htmlescape(text).replace(/\n/g, '<br>');
}


$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
            // Only send the token to relative URLs i.e. locally.
            xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
        }
    }
});


function getNumberFromElement(el, prefix) {
    var cls = el.attr('class');
    if (cls == undefined)
        cls = el[0].className; // IE7
    var parts = cls.split(' ');
    var regex = new RegExp(prefix+'_(\\d+)')
    for (i in parts)
    {
        var match = parts[i].match(regex);
        if (match)
            return parseInt(match[1])
    }
}


(function($){  
$.fn.placeholder = function(label, options) {  
    var defaults = {
        className: 'placeholder'
    };
    var options = $.extend(defaults, options);
    return this.each(function() {  
        var obj = $(this);

        if (obj[0]._placeholder)
            return;
        obj[0]._placeholder = true;

        obj.wrap('<span class="placeholder-wrapper" />')

        var text = obj.attr('placeholder');
        if (!text) return;

        var span = $('<span>').attr('class', options.className).html(linebreaksbr(html)).click(function() {
            obj.focus();
        });
        span.insertBefore(obj);
        obj.attr('placeholder','').keydown(function(ev) {
            setTimeout(function() {
                if (obj.val().length > 0)
                    span.hide();
                else
                    span.show();
            }, 0);
        }).focus(function() {
            span.addClass('focused');
        }).blur(function() {
            span.removeClass('focused');
        });
        if (obj.val().length > 0)
            span.hide();
    });  
};  
})(jQuery); 


function popup(link, w, h, name)
{
    var url;
    if (link.getAttribute)
    {
        url = link.getAttribute('href');
        if (url.indexOf('?') == -1)
            url = url + '?popup=true';
        else
            url = url + '&popup=true';
    }
    else
        url = link;
    var x = screen.availWidth/2-w/2;
    var y = screen.availHeight/2-h/2;
    var target = name || 'popup';
    window.open(url, target, 'toolbar=0,location=1,status=0,menubar=0,scrollbars=1,resizable=1,width='+w+',height='+h+',top='+y+',screenX='+x+',screenY='+y);
    return false;
}

$.fn.spin = function(opts) {
  this.each(function() {
    var $this = $(this),
        spinner = $this.data('spinner');

    if (spinner) spinner.stop();
    if (opts !== false) {
      opts = $.extend({color: $this.css('color')}, opts);
      spinner = new Spinner(opts).spin(this);
      $this.data('spinner', spinner);
    }
  });
  return this;
};


function appendToGet(key, value)
{
    key = escape(key); value = escape(value);

    var kvp = document.location.search.substr(1).split('&');

    kvp = kvp[0] && kvp || [];

    var i=kvp.length; var x; while(i--) 
    {
        x = kvp[i].split('=');

        if (x[0]==key)
        {
                x[1] = value;
                kvp[i] = x.join('=');
                break;
        }
    }

    if(i<0) {kvp[kvp.length] = [key,value].join('=');}

    return kvp.join('&'); 
}

$(function() {
    $('ul.nav>li.menu').click(function(ev) {
        $(this).toggleClass('open');
        ev.preventDefault;
    });
});
