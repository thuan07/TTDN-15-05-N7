/** @odoo-module alias=website.root */

import ajax from 'web.ajax';
import { _t } from 'web.core';
import KeyboardNavigationMixin from 'web.KeyboardNavigationMixin';
import {Markup} from 'web.utils';
import session from 'web.session';
import publicRootData from 'web.public.root';
import "web.zoomodoo";
import { FullscreenIndication } from '@website/js/widgets/fullscreen_indication';

export const WebsiteRoot = publicRootData.PublicRoot.extend(KeyboardNavigationMixin, {
    // TODO remove KeyboardNavigationMixin in master
    events: _.extend({}, KeyboardNavigationMixin.events, publicRootData.PublicRoot.prototype.events || {}, {
        'click .js_change_lang': '_onLangChangeClick',
        'click .js_publish_management .js_publish_btn': '_onPublishBtnClick',
        'click .js_multi_website_switch': '_onWebsiteSwitch',
        'shown.bs.modal': '_onModalShown',
    }),
    custom_events: _.extend({}, publicRootData.PublicRoot.prototype.custom_events || {}, {
        'gmap_api_request': '_onGMapAPIRequest',
        'gmap_api_key_request': '_onGMapAPIKeyRequest',
        'ready_to_clean_for_save': '_onWidgetsStopRequest',
        'seo_object_request': '_onSeoObjectRequest',
        'will_remove_snippet': '_onWidgetsStopRequest',
    }),

    /**
     * @override
     */
    init() {
        this.isFullscreen = false;
        KeyboardNavigationMixin.init.call(this, {
            autoAccessKeys: false,
            skipRenderOverlay: true,
        });

        // Special case for Safari browser: padding on wrapwrap is added by the
        // layout option (boxed, etc), but it also receives a border on top of
        // it to simulate an addition of padding. That padding is added with
        // the "sidebar" header template to combine both options/effects.
        // Sadly, the border hack is not working on safari, the menu is somehow
        // broken and its content is not visible.
        // This class will be used in scss to instead add the border size to the
        // padding directly on Safari when "sidebar" menu is enabled.
        if (/^((?!chrome|android).)*safari/i.test(navigator.userAgent) && document.querySelector('#wrapwrap')) {
            document.querySelector('#wrapwrap').classList.add('o_safari_browser');
        }

        return this._super(...arguments);
    },
    /**
     * @override
     */
    willStart: async function () {
        this.fullscreenIndication = new FullscreenIndication(this);
        return Promise.all([
            this._super(...arguments),
            this.fullscreenIndication.appendTo(document.body),
        ]);
    },
    /**
     * @override
     */
    start: function () {
        KeyboardNavigationMixin.start.call(this);
        // Compatibility lang change ?
        if (!this.$('.js_change_lang').length) {
            var $links = this.$('.js_language_selector a:not([data-oe-id])');
            var m = $(_.min($links, function (l) {
                return $(l).attr('href').length;
            })).attr('href');
            $links.each(function () {
                var $link = $(this);
                var t = $link.attr('href');
                var l = (t === m) ? "default" : t.split('/')[1];
                $link.data('lang', l).addClass('js_change_lang');
            });
        }

        // Enable magnify on zommable img
        this.$('.zoomable img[data-zoom]').zoomOdoo();

        return this._super.apply(this, arguments);
    },
    /**
     * @override
     */
    destroy() {
        KeyboardNavigationMixin.destroy.call(this);
        return this._super(...arguments);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    _getContext: function (context) {
        var html = document.documentElement;
        return _.extend({
            'website_id': html.getAttribute('data-website-id') | 0,
        }, this._super.apply(this, arguments));
    },
    /**
     * @override
     */
    _getExtraContext: function (context) {
        var html = document.documentElement;
        return _.extend({
            'editable': !!(html.dataset.editable || $('[data-oe-model]').length), // temporary hack, this should be done in python
            'translatable': !!html.dataset.translatable,
            'edit_translations': !!html.dataset.edit_translations,
        }, this._super.apply(this, arguments));
    },
    /**
     * @private
     * @param {boolean} [refetch=false]
     */
    async _getGMapAPIKey(refetch) {
        if (refetch || !this._gmapAPIKeyProm) {
            this._gmapAPIKeyProm = new Promise(async resolve => {
                const data = await this._rpc({
                    route: '/website/google_maps_api_key',
                });
                resolve(JSON.parse(data).google_maps_api_key || '');
            });
        }
        return this._gmapAPIKeyProm;
    },
    /**
     * @override
     */
    _getPublicWidgetsRegistry: function (options) {
        var registry = this._super.apply(this, arguments);
        if (options.editableMode) {
            return _.pick(registry, function (PublicWidget) {
                return !PublicWidget.prototype.disabledInEditableMode;
            });
        }
        return registry;
    },
    /**
     * @private
     * @param {boolean} [editableMode=false]
     * @param {boolean} [refetch=false]
     */
    async _loadGMapAPI(editableMode, refetch) {
        // Note: only need refetch to reload a configured key and load the
        // library. If the library was loaded with a correct key and that the
        // key changes meanwhile... it will not work but we can agree the user
        // can bother to reload the page at that moment.
        if (refetch || !this._gmapAPILoading) {
            this._gmapAPILoading = new Promise(async resolve => {
                const key = await this._getGMapAPIKey(refetch);

                window.odoo_gmap_api_post_load = (async function odoo_gmap_api_post_load() {
                    await this._startWidgets(undefined, {editableMode: editableMode});
                    resolve(key);
                }).bind(this);

                if (!key) {
                    if (!editableMode && session.is_admin) {
                        const message = _t("Cannot load google map.");
                        const urlTitle = _t("Check your configuration.");
                        this.displayNotification({
                            type: 'warning',
                            sticky: true,
                            message:
                                Markup`<div>
                                    <span>${message}</span><br/>
                                    <a href="/web#action=website.action_website_configuration">${urlTitle}</a>
                                </div>`,
                        });
                    }
                    resolve(false);
                    this._gmapAPILoading = false;
                    return;
                }
                await ajax.loadJS(`https://maps.googleapis.com/maps/api/js?v=3.exp&libraries=places&callback=odoo_gmap_api_post_load&key=${encodeURIComponent(key)}`);
            });
        }
        return this._gmapAPILoading;
    },
    /**
     * Toggles the fullscreen mode.
     *
     * @private
     * @param {boolean} state toggle fullscreen on/off (true/false)
     */
    _toggleFullscreen(state) {
        this.isFullscreen = state;
        if (this.isFullscreen) {
            this.fullscreenIndication.show();
        } else {
            this.fullscreenIndication.hide();
        }
        document.body.classList.add('o_fullscreen_transition');
        document.body.classList.toggle('o_fullscreen', this.isFullscreen);
        document.body.style.overflowX = 'hidden';
        let resizing = true;
        window.requestAnimationFrame(function resizeFunction() {
            window.dispatchEvent(new Event('resize'));
            if (resizing) {
                window.requestAnimationFrame(resizeFunction);
            }
        });
        let stopResizing;
        const onTransitionEnd = ev => {
            if (ev.target === document.body && ev.propertyName === 'padding-top') {
                stopResizing();
            }
        };
        stopResizing = () => {
            resizing = false;
            document.body.style.overflowX = '';
            document.body.removeEventListener('transitionend', onTransitionEnd);
            document.body.classList.remove('o_fullscreen_transition');
        };
        document.body.addEventListener('transitionend', onTransitionEnd);
        // Safeguard in case the transitionend event doesn't trigger for whatever reason.
        window.setTimeout(() => stopResizing(), 500);
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    _onWidgetsStartRequest: function (ev) {
        ev.data.options = _.clone(ev.data.options || {});
        ev.data.options.editableMode = ev.data.editableMode;
        this._super.apply(this, arguments);
    },
    /**
     * @todo review
     * @private
     */
    _onLangChangeClick: function (ev) {
        ev.preventDefault();

        var $target = $(ev.currentTarget);
        // retrieve the hash before the redirect
        var redirect = {
            lang: encodeURIComponent($target.data('url_code')),
            url: encodeURIComponent($target.attr('href').replace(/[&?]edit_translations[^&?]+/, '')),
            hash: encodeURIComponent(window.location.hash)
        };
        window.location.href = _.str.sprintf("/website/lang/%(lang)s?r=%(url)s%(hash)s", redirect);
    },
    /**
     * @private
     * @param {OdooEvent} ev
     */
    async _onGMapAPIRequest(ev) {
        ev.stopPropagation();
        const apiKey = await this._loadGMapAPI(ev.data.editableMode, ev.data.refetch);
        ev.data.onSuccess(apiKey);
    },
    /**
     * @private
     * @param {OdooEvent} ev
     */
    async _onGMapAPIKeyRequest(ev) {
        ev.stopPropagation();
        const apiKey = await this._getGMapAPIKey(ev.data.refetch);
        ev.data.onSuccess(apiKey);
    },
    /**
    /**
     * Checks information about the page SEO object.
     *
     * @private
     * @param {OdooEvent} ev
     */
    _onSeoObjectRequest: function (ev) {
        var res = this._unslugHtmlDataObject('seo-object');
        ev.data.callback(res);
    },
    /**
     * Returns a model/id object constructed from html data attribute.
     *
     * @private
     * @param {string} dataAttr
     * @returns {Object} an object with 2 keys: model and id, or null
     * if not found
     */
    _unslugHtmlDataObject: function (dataAttr) {
        var repr = $('html').data(dataAttr);
        var match = repr && repr.match(/(.+)\((\d+),(.*)\)/);
        if (!match) {
            return null;
        }
        return {
            model: match[1],
            id: match[2] | 0,
        };
    },
    /**
     * @todo review
     * @private
     */
    _onPublishBtnClick: function (ev) {
        ev.preventDefault();
        if (document.body.classList.contains('editor_enable')) {
            return;
        }

        var self = this;
        var $data = $(ev.currentTarget).parents(".js_publish_management:first");
        this._rpc({
            route: $data.data('controller') || '/website/publish',
            params: {
                id: +$data.data('id'),
                object: $data.data('object'),
            },
        })
        .then(function (result) {
            $data.toggleClass("css_published", result).toggleClass("css_unpublished", !result);
            $data.find('input').prop("checked", result);
            $data.parents("[data-publish]").attr("data-publish", +result ? 'on' : 'off');
        });
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onWebsiteSwitch: function (ev) {
        var websiteId = ev.currentTarget.getAttribute('website-id');
        var websiteDomain = ev.currentTarget.getAttribute('domain');
        let url = `/website/force/${encodeURIComponent(websiteId)}`;
        if (websiteDomain && window.location.hostname !== websiteDomain) {
            url = websiteDomain + url;
        }
        const path = window.location.pathname + window.location.search + window.location.hash;
        window.location.href = $.param.querystring(url, {'path': path});
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onModalShown: function (ev) {
        $(ev.target).addClass('modal_shown');
    },
    /**
     * @override
     */
    _onKeyDown(ev) {
        if (!session.user_id) {
            return;
        }
        // If document.body doesn't contain the element, it was probably removed as a consequence of pressing Esc.
        // we don't want to toggle fullscreen as the removal (eg, closing a modal) is the intended action.
        if (ev.keyCode !== $.ui.keyCode.ESCAPE || !document.body.contains(ev.target) || ev.target.closest('.modal')) {
            return KeyboardNavigationMixin._onKeyDown.apply(this, arguments);
        }
        this._toggleFullscreen(!this.isFullscreen);
    },
});

export default {
    WebsiteRoot: WebsiteRoot,
};
