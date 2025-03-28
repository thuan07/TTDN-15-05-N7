odoo.define('point_of_sale.CashOpeningPopup', function(require) {
    'use strict';

    const { useState, useRef } = owl.hooks;
    const { useValidateCashInput } = require('point_of_sale.custom_hooks');
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { parse } = require('web.field_utils');


    class CashOpeningPopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.manualInputCashCount = null;
            this.state = useState({
                notes: "",
                openingCash: this.env.pos.bank_statement.balance_start || 0,
            });
            this.moneyDetailsRef = useRef('moneyDetails');
            this.openingCashInputRef = useRef('openingCashInput');
            useValidateCashInput("openingCashInput", this.env.pos.bank_statement.balance_start);
        }
        openDetailsPopup() {
            if (this.moneyDetailsRef.comp.isClosed()){
                this.moneyDetailsRef.comp.openPopup();
                this.state.openingCash = 0;
                this.state.notes = "";
                if (this.manualInputCashCount) {
                    this.moneyDetailsRef.comp.reset();
                }
            }
        }
        startSession() {
            this.env.pos.bank_statement.balance_start = this.state.openingCash;
            this.env.pos.pos_session.state = 'opened';
            this.rpc({
                   model: 'pos.session',
                    method: 'set_cashbox_pos',
                    args: [this.env.pos.pos_session.id, this.state.openingCash, this.state.notes],
                });
            this.cancel(); // close popup
        }
        updateCashOpening(event) {
            const { total, moneyDetailsNotes } = event.detail;
            this.openingCashInputRef.el.value = this.env.pos.format_currency_no_symbol(total);
            this.state.openingCash = total;
            if (moneyDetailsNotes) {
                this.state.notes = moneyDetailsNotes;
            }
            this.manualInputCashCount = false;
        }
        handleInputChange(event) {
            if (event.target.classList.contains('invalid-cash-input')) return;
            this.manualInputCashCount = true;
            this.state.openingCash = parse.float(event.target.value);
        }
    }

    CashOpeningPopup.template = 'CashOpeningPopup';
    Registries.Component.add(CashOpeningPopup);

    return CashOpeningPopup;
});
