var floatSubMenuTimeout, targetFloatMenu, handleSlimScroll = function() {
	"use strict";
	$.when($("[data-scrollbar=true]").each(function() {
		generateSlimScroll($(this))
	})).done(function() {
		$('[data-scrollbar="true"]').mouseover()
	})
},
handleSidebarMenu = function() {
	"use strict";
	var t = $(".sidebar").attr("data-disable-slide-animation") ? 0 : 250;
	$(".sidebar .nav > .has-sub > a").click(function() {
		var a = $(this).next(".sub-menu"),
		e = $(".sidebar .nav > li.has-sub > .sub-menu").not(a);
		0 === $(".page-sidebar-minified").length && ($(e).closest("li").addClass("closing"), $(e).slideUp(t, function() {
			$(e).closest("li").addClass("closed").removeClass("expand closing")
		}), $(a).is(":visible") ? $(a).closest("li").addClass("closing").removeClass("expand") : $(a).closest("li").addClass("expanding").removeClass("closed"), $(a).slideToggle(t, function() {
			var e = $(this).closest("li");
			$(a).is(":visible") ? ($(e).addClass("expand"), $(e).removeClass("closed")) : ($(e).addClass("closed"), $(e).removeClass("expand")), $(e).removeClass("expanding closing")
		}))
	}), $(".sidebar .nav > .has-sub .sub-menu li.has-sub > a").click(function() {
		if (0 === $(".page-sidebar-minified").length) {
			var a = $(this).next(".sub-menu");
			$(a).is(":visible") ? $(a).closest("li").addClass("closing").removeClass("expand") : $(a).closest("li").addClass("expanding").removeClass("closed"), $(a).slideToggle(t, function() {
				var e = $(this).closest("li");
				$(a).is(":visible") ? ($(e).addClass("expand"), $(e).removeClass("closed")) : ($(e).addClass("closed"), $(e).removeClass("expand")), $(e).removeClass("expanding closing")
			})
		}
	})
},
handleMobileSidebarToggle = function() {
	var n = !1;
	$(".sidebar").bind("click touchstart", function(e) {
		0 !== $(e.target).closest(".sidebar").length ? n = !0 : (n = !1, e.stopPropagation())
	}), $(document).bind("click touchstart", function(e) {
		0 === $(e.target).closest(".sidebar").length && (n = !1), 0 !== $(e.target).closest("#float-sub-menu").length && (n = !0), e.isPropagationStopped() || !0 === n || ($("#page-container").hasClass("page-sidebar-toggled") && (n = !0, $("#page-container").removeClass("page-sidebar-toggled")), $(window).width() <= 767 && $("#page-container").hasClass("page-right-sidebar-toggled") && (n = !0, $("#page-container").removeClass("page-right-sidebar-toggled")))
	}), $("[data-click=right-sidebar-toggled]").click(function(e) {
		e.stopPropagation();
		var a = "#page-container",
		t = "page-right-sidebar-collapsed";
		t = $(window).width() < 979 ? "page-right-sidebar-toggled" : t, $(a).hasClass(t) ? $(a).removeClass(t) : !0 !== n ? $(a).addClass(t) : n = !1, $(window).width() < 480 && $("#page-container").removeClass("page-sidebar-toggled"), $(window).trigger("resize")
	}), $("[data-click=sidebar-toggled]").click(function(e) {
		e.stopPropagation();
		var a = "page-sidebar-toggled",
		t = "#page-container";
		$(t).hasClass(a) ? $(t).removeClass(a) : !0 !== n ? $(t).addClass(a) : n = !1, $(window).width() < 480 && $("#page-container").removeClass("page-right-sidebar-toggled")
	})
},
handleSidebarMinify = function() {
	$(document).on("click", "[data-click=sidebar-minify]", function(e) {
		e.preventDefault();
		var a = "page-sidebar-minified",
		t = "#page-container";
		$(t).hasClass(a) ? $(t).removeClass(a) : ($(t).addClass(a), /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) && ($('#sidebar [data-scrollbar="true"]').css("margin-top", "0"), $('#sidebar [data-scrollbar="true"]').css("overflow-x", "scroll"))), $(window).trigger("resize")
	})
},
handleLocalStorage = function() {
	"use strict";
	try {
		if ("undefined" != typeof Storage && "undefined" != typeof localStorage) {
			var e = window.location.href;
			e = (e = e.split("?"))[0];
			var a = localStorage.getItem(e);
			if (a) {
				a = JSON.parse(a);
				var t = 0;
				$.when($('.panel:not([data-sortable="false"])').parent('[class*="col-"]').each(function() {
					var e = a[t],
					o = $(this);
					e && $.each(e, function(e, a) {
						var t = $('[data-sortable-id="' + a.id + '"]').not('[data-init="true"]');
						if (0 !== $(t).length) {
							var n = $(t).clone();
							$(t).remove(), $(o).append(n), $('[data-sortable-id="' + a.id + '"]').attr("data-init", "true")
						}
					}), t++
				})).done(function() {
					window.dispatchEvent(new CustomEvent("localstorage-position-loaded"))
				})
			}
		} else alert("Your browser is not supported with the local storage")
	} catch (e) {
		console.log(e)
	}
},
handleClearSidebarSelection = function() {
	$(".sidebar .nav > li, .sidebar .nav .sub-menu").removeClass("expand").removeAttr("style")
},
handlePageScrollClass = function() {
	$(window).on("scroll", function() {
		handleCheckScrollClass()
	}), handleCheckScrollClass()
},
handleMouseoverFloatSubMenu = function(e) {
	clearTimeout(floatSubMenuTimeout)
},
handleMouseoutFloatSubMenu = function(e) {
	floatSubMenuTimeout = setTimeout(function() {
		$("#float-sub-menu").remove()
	}, 150)
},
handleSidebarMinifyFloatMenu = function() {
	$(document).on("click", "#float-sub-menu li.has-sub > a", function(e) {
		var a = $(this).next(".sub-menu"),
		t = $(a).closest("li"),
		r = !1,
		d = !1;
		$(a).is(":visible") ? ($(t).addClass("closing"), r = !0) : ($(t).addClass("expanding"), d = !0), $(a).slideToggle({
			duration: 250,
			progress: function() {
				var e = $("#float-sub-menu"),
				a = $(e).height(),
				t = $(e).offset(),
				n = $(e).attr("data-offset-top"),
				o = $(e).attr("data-menu-offset-top"),
				i = t.top - $(window).scrollTop(),
				s = $(window).height();
				if (r && n < i && (i = n < i ? n : i, $("#float-sub-menu").css({
					top: i + "px",
					bottom: "auto"
				}), $("#float-sub-menu-arrow").css({
					top: "20px",
					bottom: "auto"
				}), $("#float-sub-menu-line").css({
					top: "20px",
					bottom: "auto"
				})), d && s - i < a) {
					var l = s - o - 22;
					$("#float-sub-menu").css({
						top: "auto",
						bottom: 0
					}), $("#float-sub-menu-arrow").css({
						top: "auto",
						bottom: l + "px"
					}), $("#float-sub-menu-line").css({
						top: "20px",
						bottom: l + "px"
					})
				}
			},
			complete: function() {
				$(a).is(":visible") ? $(t).addClass("expand") : $(t).addClass("closed"), $(t).removeClass("closing expanding")
			}
		})
	}), $(".sidebar .nav > li.has-sub > a").hover(function() {
		if ($("#page-container").hasClass("page-sidebar-minified")) {
			clearTimeout(floatSubMenuTimeout);
			var e = $(this).closest("li").find(".sub-menu").first();
			if (targetFloatMenu == this && 0 !== $("#float-sub-menu").length) return;
			targetFloatMenu = this;
			var a = $(e).html();
			if (a) {
				var t = $("#sidebar").offset(),
				n = $("#page-container").hasClass("page-with-right-sidebar") ? $(window).width() - t.left : t.left + 60,
				o = $(e).height(),
				i = $(this).offset().top - $(window).scrollTop(),
				s = $("#page-container").hasClass("page-with-right-sidebar") ? "auto" : n,
				l = $("#page-container").hasClass("page-with-right-sidebar") ? n : "auto",
				r = $(window).height();
				if (0 === $("#float-sub-menu").length ? (a = '<div class="float-sub-menu-container" id="float-sub-menu" data-offset-top="' + i + '" data-menu-offset-top="' + i + '" onmouseover="handleMouseoverFloatSubMenu(this)" onmouseout="handleMouseoutFloatSubMenu(this)">\t<div class="float-sub-menu-arrow" id="float-sub-menu-arrow"></div>\t<div class="float-sub-menu-line" id="float-sub-menu-line"></div>\t<ul class="float-sub-menu">' + a + "</ul></div>", $("#page-container").append(a)) : ($("#float-sub-menu").attr("data-offset-top", i), $("#float-sub-menu").attr("data-menu-offset-top", i), $(".float-sub-menu").html(a)), o < r - i) $("#float-sub-menu").css({
					top: i,
					left: s,
					bottom: "auto",
					right: l
				}), $("#float-sub-menu-arrow").css({
					top: "20px",
					bottom: "auto"
				}), $("#float-sub-menu-line").css({
					top: "20px",
					bottom: "auto"
				});
				else {
					$("#float-sub-menu").css({
						bottom: 0,
						top: "auto",
						left: s,
						right: l
					});
					var d = r - i - 21;
					$("#float-sub-menu-arrow").css({
						top: "auto",
						bottom: d + "px"
					}), $("#float-sub-menu-line").css({
						top: "20px",
						bottom: d + "px"
					})
				}
			} else $("#float-sub-menu").remove(), targetFloatMenu = ""
		}
	}, function() {
		$("#page-container").hasClass("page-sidebar-minified") && (floatSubMenuTimeout = setTimeout(function() {
			$("#float-sub-menu").remove(), targetFloatMenu = ""
		}, 250))
	})
},
CLEAR_OPTION = "",
handleSetPageOption = function(e) {
	e.pageContentFullHeight && $("#page-container").addClass("page-content-full-height"), e.pageSidebarLight && $("#page-container").addClass("page-with-light-sidebar"), e.pageSidebarRight && $("#page-container").addClass("page-with-right-sidebar"), e.pageSidebarWide && $("#page-container").addClass("page-with-wide-sidebar"), e.pageSidebarMinified && $("#page-container").addClass("page-sidebar-minified"), e.pageSidebarTransparent && $("#sidebar").addClass("sidebar-transparent"), e.pageContentFullWidth && $("#content").addClass("content-full-width"), e.pageContentInverseMode && $("#content").addClass("content-inverse-mode"), e.pageBoxedLayout && $("body").addClass("boxed-layout"), e.clearOptionOnLeave && (CLEAR_OPTION = e)
},
handleClearPageOption = function(e) {
	e.pageContentFullHeight && $("#page-container").removeClass("page-content-full-height"), e.pageSidebarLight && $("#page-container").removeClass("page-with-light-sidebar"), e.pageSidebarRight && $("#page-container").removeClass("page-with-right-sidebar"), e.pageSidebarWide && $("#page-container").removeClass("page-with-wide-sidebar"), e.pageSidebarMinified && $("#page-container").removeClass("page-sidebar-minified"), e.pageSidebarTransparent && $("#sidebar").removeClass("sidebar-transparent"), e.pageContentFullWidth && $("#content").removeClass("content-full-width"), e.pageContentInverseMode && $("#content").removeClass("content-inverse-mode"), e.pageBoxedLayout && $("body").removeClass("boxed-layout")
},
App = function() {
	"use strict";
	var a;
	return {
		init: function(e) {
			e && (a = e), this.initLocalStorage(), this.initSidebar(), this.initTopMenu(), this.initComponent(), this.initThemePanel(), this.initPageLoad(), $(window).trigger("load"), a && a.ajaxMode && this.initAjax()
		},
		initSidebar: function() {
			handleSidebarMenu(), handleMobileSidebarToggle(), handleSidebarMinify(), handleSidebarMinifyFloatMenu(), handleToggleNavProfile(), handleToggleNavbarSearch(), (!a || a && !a.disableSidebarScrollMemory) && handleSidebarScrollMemory()
		},
		initSidebarSelection: function() {
			handleClearSidebarSelection()
		},
		initComponent: function() {
			(!a || a && !a.disableDraggablePanel) && handleSlimScroll(), handleUnlimitedTabsRender(), handlePanelAction(), handleScrollToTopButton(), handleAfterPageLoadAddClass(), handlePageScrollClass(), 767 < $(window).width() && handelTooltipPopoverActivation()
		},
		initLocalStorage: function() {
			(!a || a && !a.disableLocalStorage) && handleLocalStorage()
		},
		initAjax: function() {
			handleAjaxMode(a), $.ajaxSetup({
				cache: !0
			})
		},
		scrollTop: function() {
			$("html, body").animate({
				scrollTop: $("body").offset().top
			}, 0)
		}
	}
}();
$(document).ready(function() {
	App.init();
	Highlight.init();
});