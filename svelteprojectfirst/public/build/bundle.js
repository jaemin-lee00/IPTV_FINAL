
(function(l, r) { if (!l || l.getElementById('livereloadscript')) return; r = l.createElement('script'); r.async = 1; r.src = '//' + (self.location.host || 'localhost').split(':')[0] + ':35729/livereload.js?snipver=1'; r.id = 'livereloadscript'; l.getElementsByTagName('head')[0].appendChild(r) })(self.document);
var app = (function () {
    'use strict';

    function noop() { }
    function add_location(element, file, line, column, char) {
        element.__svelte_meta = {
            loc: { file, line, column, char }
        };
    }
    function run(fn) {
        return fn();
    }
    function blank_object() {
        return Object.create(null);
    }
    function run_all(fns) {
        fns.forEach(run);
    }
    function is_function(thing) {
        return typeof thing === 'function';
    }
    function safe_not_equal(a, b) {
        return a != a ? b == b : a !== b || ((a && typeof a === 'object') || typeof a === 'function');
    }
    let src_url_equal_anchor;
    function src_url_equal(element_src, url) {
        if (!src_url_equal_anchor) {
            src_url_equal_anchor = document.createElement('a');
        }
        src_url_equal_anchor.href = url;
        return element_src === src_url_equal_anchor.href;
    }
    function is_empty(obj) {
        return Object.keys(obj).length === 0;
    }
    function action_destroyer(action_result) {
        return action_result && is_function(action_result.destroy) ? action_result.destroy : noop;
    }

    const globals = (typeof window !== 'undefined'
        ? window
        : typeof globalThis !== 'undefined'
            ? globalThis
            : global);
    function append(target, node) {
        target.appendChild(node);
    }
    function insert(target, node, anchor) {
        target.insertBefore(node, anchor || null);
    }
    function detach(node) {
        if (node.parentNode) {
            node.parentNode.removeChild(node);
        }
    }
    function destroy_each(iterations, detaching) {
        for (let i = 0; i < iterations.length; i += 1) {
            if (iterations[i])
                iterations[i].d(detaching);
        }
    }
    function element(name) {
        return document.createElement(name);
    }
    function text(data) {
        return document.createTextNode(data);
    }
    function space() {
        return text(' ');
    }
    function listen(node, event, handler, options) {
        node.addEventListener(event, handler, options);
        return () => node.removeEventListener(event, handler, options);
    }
    function attr(node, attribute, value) {
        if (value == null)
            node.removeAttribute(attribute);
        else if (node.getAttribute(attribute) !== value)
            node.setAttribute(attribute, value);
    }
    function to_number(value) {
        return value === '' ? null : +value;
    }
    function children(element) {
        return Array.from(element.childNodes);
    }
    function set_input_value(input, value) {
        input.value = value == null ? '' : value;
    }
    function toggle_class(element, name, toggle) {
        element.classList[toggle ? 'add' : 'remove'](name);
    }
    function custom_event(type, detail, { bubbles = false, cancelable = false } = {}) {
        const e = document.createEvent('CustomEvent');
        e.initCustomEvent(type, bubbles, cancelable, detail);
        return e;
    }

    let current_component;
    function set_current_component(component) {
        current_component = component;
    }
    function get_current_component() {
        if (!current_component)
            throw new Error('Function called outside component initialization');
        return current_component;
    }
    /**
     * The `onMount` function schedules a callback to run as soon as the component has been mounted to the DOM.
     * It must be called during the component's initialisation (but doesn't need to live *inside* the component;
     * it can be called from an external module).
     *
     * `onMount` does not run inside a [server-side component](/docs#run-time-server-side-component-api).
     *
     * https://svelte.dev/docs#run-time-svelte-onmount
     */
    function onMount(fn) {
        get_current_component().$$.on_mount.push(fn);
    }
    /**
     * Creates an event dispatcher that can be used to dispatch [component events](/docs#template-syntax-component-directives-on-eventname).
     * Event dispatchers are functions that can take two arguments: `name` and `detail`.
     *
     * Component events created with `createEventDispatcher` create a
     * [CustomEvent](https://developer.mozilla.org/en-US/docs/Web/API/CustomEvent).
     * These events do not [bubble](https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Building_blocks/Events#Event_bubbling_and_capture).
     * The `detail` argument corresponds to the [CustomEvent.detail](https://developer.mozilla.org/en-US/docs/Web/API/CustomEvent/detail)
     * property and can contain any type of data.
     *
     * https://svelte.dev/docs#run-time-svelte-createeventdispatcher
     */
    function createEventDispatcher() {
        const component = get_current_component();
        return (type, detail, { cancelable = false } = {}) => {
            const callbacks = component.$$.callbacks[type];
            if (callbacks) {
                // TODO are there situations where events could be dispatched
                // in a server (non-DOM) environment?
                const event = custom_event(type, detail, { cancelable });
                callbacks.slice().forEach(fn => {
                    fn.call(component, event);
                });
                return !event.defaultPrevented;
            }
            return true;
        };
    }

    const dirty_components = [];
    const binding_callbacks = [];
    let render_callbacks = [];
    const flush_callbacks = [];
    const resolved_promise = /* @__PURE__ */ Promise.resolve();
    let update_scheduled = false;
    function schedule_update() {
        if (!update_scheduled) {
            update_scheduled = true;
            resolved_promise.then(flush);
        }
    }
    function add_render_callback(fn) {
        render_callbacks.push(fn);
    }
    // flush() calls callbacks in this order:
    // 1. All beforeUpdate callbacks, in order: parents before children
    // 2. All bind:this callbacks, in reverse order: children before parents.
    // 3. All afterUpdate callbacks, in order: parents before children. EXCEPT
    //    for afterUpdates called during the initial onMount, which are called in
    //    reverse order: children before parents.
    // Since callbacks might update component values, which could trigger another
    // call to flush(), the following steps guard against this:
    // 1. During beforeUpdate, any updated components will be added to the
    //    dirty_components array and will cause a reentrant call to flush(). Because
    //    the flush index is kept outside the function, the reentrant call will pick
    //    up where the earlier call left off and go through all dirty components. The
    //    current_component value is saved and restored so that the reentrant call will
    //    not interfere with the "parent" flush() call.
    // 2. bind:this callbacks cannot trigger new flush() calls.
    // 3. During afterUpdate, any updated components will NOT have their afterUpdate
    //    callback called a second time; the seen_callbacks set, outside the flush()
    //    function, guarantees this behavior.
    const seen_callbacks = new Set();
    let flushidx = 0; // Do *not* move this inside the flush() function
    function flush() {
        // Do not reenter flush while dirty components are updated, as this can
        // result in an infinite loop. Instead, let the inner flush handle it.
        // Reentrancy is ok afterwards for bindings etc.
        if (flushidx !== 0) {
            return;
        }
        const saved_component = current_component;
        do {
            // first, call beforeUpdate functions
            // and update components
            try {
                while (flushidx < dirty_components.length) {
                    const component = dirty_components[flushidx];
                    flushidx++;
                    set_current_component(component);
                    update(component.$$);
                }
            }
            catch (e) {
                // reset dirty state to not end up in a deadlocked state and then rethrow
                dirty_components.length = 0;
                flushidx = 0;
                throw e;
            }
            set_current_component(null);
            dirty_components.length = 0;
            flushidx = 0;
            while (binding_callbacks.length)
                binding_callbacks.pop()();
            // then, once components are updated, call
            // afterUpdate functions. This may cause
            // subsequent updates...
            for (let i = 0; i < render_callbacks.length; i += 1) {
                const callback = render_callbacks[i];
                if (!seen_callbacks.has(callback)) {
                    // ...so guard against infinite loops
                    seen_callbacks.add(callback);
                    callback();
                }
            }
            render_callbacks.length = 0;
        } while (dirty_components.length);
        while (flush_callbacks.length) {
            flush_callbacks.pop()();
        }
        update_scheduled = false;
        seen_callbacks.clear();
        set_current_component(saved_component);
    }
    function update($$) {
        if ($$.fragment !== null) {
            $$.update();
            run_all($$.before_update);
            const dirty = $$.dirty;
            $$.dirty = [-1];
            $$.fragment && $$.fragment.p($$.ctx, dirty);
            $$.after_update.forEach(add_render_callback);
        }
    }
    /**
     * Useful for example to execute remaining `afterUpdate` callbacks before executing `destroy`.
     */
    function flush_render_callbacks(fns) {
        const filtered = [];
        const targets = [];
        render_callbacks.forEach((c) => fns.indexOf(c) === -1 ? filtered.push(c) : targets.push(c));
        targets.forEach((c) => c());
        render_callbacks = filtered;
    }
    const outroing = new Set();
    let outros;
    function group_outros() {
        outros = {
            r: 0,
            c: [],
            p: outros // parent group
        };
    }
    function check_outros() {
        if (!outros.r) {
            run_all(outros.c);
        }
        outros = outros.p;
    }
    function transition_in(block, local) {
        if (block && block.i) {
            outroing.delete(block);
            block.i(local);
        }
    }
    function transition_out(block, local, detach, callback) {
        if (block && block.o) {
            if (outroing.has(block))
                return;
            outroing.add(block);
            outros.c.push(() => {
                outroing.delete(block);
                if (callback) {
                    if (detach)
                        block.d(1);
                    callback();
                }
            });
            block.o(local);
        }
        else if (callback) {
            callback();
        }
    }
    function create_component(block) {
        block && block.c();
    }
    function mount_component(component, target, anchor, customElement) {
        const { fragment, after_update } = component.$$;
        fragment && fragment.m(target, anchor);
        if (!customElement) {
            // onMount happens before the initial afterUpdate
            add_render_callback(() => {
                const new_on_destroy = component.$$.on_mount.map(run).filter(is_function);
                // if the component was destroyed immediately
                // it will update the `$$.on_destroy` reference to `null`.
                // the destructured on_destroy may still reference to the old array
                if (component.$$.on_destroy) {
                    component.$$.on_destroy.push(...new_on_destroy);
                }
                else {
                    // Edge case - component was destroyed immediately,
                    // most likely as a result of a binding initialising
                    run_all(new_on_destroy);
                }
                component.$$.on_mount = [];
            });
        }
        after_update.forEach(add_render_callback);
    }
    function destroy_component(component, detaching) {
        const $$ = component.$$;
        if ($$.fragment !== null) {
            flush_render_callbacks($$.after_update);
            run_all($$.on_destroy);
            $$.fragment && $$.fragment.d(detaching);
            // TODO null out other refs, including component.$$ (but need to
            // preserve final state?)
            $$.on_destroy = $$.fragment = null;
            $$.ctx = [];
        }
    }
    function make_dirty(component, i) {
        if (component.$$.dirty[0] === -1) {
            dirty_components.push(component);
            schedule_update();
            component.$$.dirty.fill(0);
        }
        component.$$.dirty[(i / 31) | 0] |= (1 << (i % 31));
    }
    function init(component, options, instance, create_fragment, not_equal, props, append_styles, dirty = [-1]) {
        const parent_component = current_component;
        set_current_component(component);
        const $$ = component.$$ = {
            fragment: null,
            ctx: [],
            // state
            props,
            update: noop,
            not_equal,
            bound: blank_object(),
            // lifecycle
            on_mount: [],
            on_destroy: [],
            on_disconnect: [],
            before_update: [],
            after_update: [],
            context: new Map(options.context || (parent_component ? parent_component.$$.context : [])),
            // everything else
            callbacks: blank_object(),
            dirty,
            skip_bound: false,
            root: options.target || parent_component.$$.root
        };
        append_styles && append_styles($$.root);
        let ready = false;
        $$.ctx = instance
            ? instance(component, options.props || {}, (i, ret, ...rest) => {
                const value = rest.length ? rest[0] : ret;
                if ($$.ctx && not_equal($$.ctx[i], $$.ctx[i] = value)) {
                    if (!$$.skip_bound && $$.bound[i])
                        $$.bound[i](value);
                    if (ready)
                        make_dirty(component, i);
                }
                return ret;
            })
            : [];
        $$.update();
        ready = true;
        run_all($$.before_update);
        // `false` as a special case of no DOM component
        $$.fragment = create_fragment ? create_fragment($$.ctx) : false;
        if (options.target) {
            if (options.hydrate) {
                const nodes = children(options.target);
                // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                $$.fragment && $$.fragment.l(nodes);
                nodes.forEach(detach);
            }
            else {
                // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                $$.fragment && $$.fragment.c();
            }
            if (options.intro)
                transition_in(component.$$.fragment);
            mount_component(component, options.target, options.anchor, options.customElement);
            flush();
        }
        set_current_component(parent_component);
    }
    /**
     * Base class for Svelte components. Used when dev=false.
     */
    class SvelteComponent {
        $destroy() {
            destroy_component(this, 1);
            this.$destroy = noop;
        }
        $on(type, callback) {
            if (!is_function(callback)) {
                return noop;
            }
            const callbacks = (this.$$.callbacks[type] || (this.$$.callbacks[type] = []));
            callbacks.push(callback);
            return () => {
                const index = callbacks.indexOf(callback);
                if (index !== -1)
                    callbacks.splice(index, 1);
            };
        }
        $set($$props) {
            if (this.$$set && !is_empty($$props)) {
                this.$$.skip_bound = true;
                this.$$set($$props);
                this.$$.skip_bound = false;
            }
        }
    }

    function dispatch_dev(type, detail) {
        document.dispatchEvent(custom_event(type, Object.assign({ version: '3.59.2' }, detail), { bubbles: true }));
    }
    function append_dev(target, node) {
        dispatch_dev('SvelteDOMInsert', { target, node });
        append(target, node);
    }
    function insert_dev(target, node, anchor) {
        dispatch_dev('SvelteDOMInsert', { target, node, anchor });
        insert(target, node, anchor);
    }
    function detach_dev(node) {
        dispatch_dev('SvelteDOMRemove', { node });
        detach(node);
    }
    function listen_dev(node, event, handler, options, has_prevent_default, has_stop_propagation, has_stop_immediate_propagation) {
        const modifiers = options === true ? ['capture'] : options ? Array.from(Object.keys(options)) : [];
        if (has_prevent_default)
            modifiers.push('preventDefault');
        if (has_stop_propagation)
            modifiers.push('stopPropagation');
        if (has_stop_immediate_propagation)
            modifiers.push('stopImmediatePropagation');
        dispatch_dev('SvelteDOMAddEventListener', { node, event, handler, modifiers });
        const dispose = listen(node, event, handler, options);
        return () => {
            dispatch_dev('SvelteDOMRemoveEventListener', { node, event, handler, modifiers });
            dispose();
        };
    }
    function attr_dev(node, attribute, value) {
        attr(node, attribute, value);
        if (value == null)
            dispatch_dev('SvelteDOMRemoveAttribute', { node, attribute });
        else
            dispatch_dev('SvelteDOMSetAttribute', { node, attribute, value });
    }
    function prop_dev(node, property, value) {
        node[property] = value;
        dispatch_dev('SvelteDOMSetProperty', { node, property, value });
    }
    function set_data_dev(text, data) {
        data = '' + data;
        if (text.data === data)
            return;
        dispatch_dev('SvelteDOMSetData', { node: text, data });
        text.data = data;
    }
    function validate_each_argument(arg) {
        if (typeof arg !== 'string' && !(arg && typeof arg === 'object' && 'length' in arg)) {
            let msg = '{#each} only iterates over array-like objects.';
            if (typeof Symbol === 'function' && arg && Symbol.iterator in arg) {
                msg += ' You can use a spread to convert this iterable into an array.';
            }
            throw new Error(msg);
        }
    }
    function validate_slots(name, slot, keys) {
        for (const slot_key of Object.keys(slot)) {
            if (!~keys.indexOf(slot_key)) {
                console.warn(`<${name}> received an unexpected slot "${slot_key}".`);
            }
        }
    }
    /**
     * Base class for Svelte components with some minor dev-enhancements. Used when dev=true.
     */
    class SvelteComponentDev extends SvelteComponent {
        constructor(options) {
            if (!options || (!options.target && !options.$$inline)) {
                throw new Error("'target' is a required option");
            }
            super();
        }
        $destroy() {
            super.$destroy();
            this.$destroy = () => {
                console.warn('Component was already destroyed'); // eslint-disable-line no-console
            };
        }
        $capture_state() { }
        $inject_state() { }
    }

    /* src\Welcome.svelte generated by Svelte v3.59.2 */
    const file$3 = "src\\Welcome.svelte";

    // (42:35) {#if showingCursor}
    function create_if_block$2(ctx) {
    	let span;

    	const block = {
    		c: function create() {
    			span = element("span");
    			span.textContent = "_";
    			attr_dev(span, "class", "cursor svelte-157kobz");
    			add_location(span, file$3, 41, 54, 999);
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, span, anchor);
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(span);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_if_block$2.name,
    		type: "if",
    		source: "(42:35) {#if showingCursor}",
    		ctx
    	});

    	return block;
    }

    function create_fragment$3(ctx) {
    	let div1;
    	let div0;
    	let h1;
    	let t0;
    	let t1;
    	let img;
    	let img_src_value;
    	let t2;
    	let button;
    	let mounted;
    	let dispose;
    	let if_block = /*showingCursor*/ ctx[1] && create_if_block$2(ctx);

    	const block = {
    		c: function create() {
    			div1 = element("div");
    			div0 = element("div");
    			h1 = element("h1");
    			t0 = text(/*displayText*/ ctx[0]);
    			if (if_block) if_block.c();
    			t1 = space();
    			img = element("img");
    			t2 = space();
    			button = element("button");
    			button.textContent = "시작하기";
    			attr_dev(h1, "class", "fade-in svelte-157kobz");
    			add_location(h1, file$3, 41, 2, 947);
    			if (!src_url_equal(img.src, img_src_value = "main_page.png")) attr_dev(img, "src", img_src_value);
    			attr_dev(img, "alt", "건강 관리 아이콘");
    			attr_dev(img, "class", "welcome-image fade-in svelte-157kobz");
    			add_location(img, file$3, 43, 2, 1061);
    			attr_dev(button, "class", "svelte-157kobz");
    			add_location(button, file$3, 45, 2, 1156);
    			attr_dev(div0, "class", "welcome svelte-157kobz");
    			add_location(div0, file$3, 39, 1, 891);
    			attr_dev(div1, "class", "background svelte-157kobz");
    			add_location(div1, file$3, 38, 0, 864);
    		},
    		l: function claim(nodes) {
    			throw new Error("options.hydrate only works if the component was compiled with the `hydratable: true` option");
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, div1, anchor);
    			append_dev(div1, div0);
    			append_dev(div0, h1);
    			append_dev(h1, t0);
    			if (if_block) if_block.m(h1, null);
    			append_dev(div0, t1);
    			append_dev(div0, img);
    			append_dev(div0, t2);
    			append_dev(div0, button);

    			if (!mounted) {
    				dispose = listen_dev(button, "click", /*handleStart*/ ctx[2], false, false, false, false);
    				mounted = true;
    			}
    		},
    		p: function update(ctx, [dirty]) {
    			if (dirty & /*displayText*/ 1) set_data_dev(t0, /*displayText*/ ctx[0]);

    			if (/*showingCursor*/ ctx[1]) {
    				if (if_block) ; else {
    					if_block = create_if_block$2(ctx);
    					if_block.c();
    					if_block.m(h1, null);
    				}
    			} else if (if_block) {
    				if_block.d(1);
    				if_block = null;
    			}
    		},
    		i: noop,
    		o: noop,
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(div1);
    			if (if_block) if_block.d();
    			mounted = false;
    			dispose();
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_fragment$3.name,
    		type: "component",
    		source: "",
    		ctx
    	});

    	return block;
    }

    function instance$3($$self, $$props, $$invalidate) {
    	let { $$slots: slots = {}, $$scope } = $$props;
    	validate_slots('Welcome', slots, []);
    	const dispatch = createEventDispatcher();

    	// 출력할 전체 텍스트
    	let text = "노인을 위한 나라에 오신 것을 환영합니다";

    	// 현재까지 표시된 텍스트를 저장할 변수
    	let displayText = "";

    	// 현재 출력 중인 글자의 인덱스
    	let currentIndex = 0;

    	// 커서 표시 여부를 결정하는 상태 변수
    	let showingCursor = false;

    	// '시작하기' 버튼 클릭 시 실행되는 함수
    	function handleStart() {
    		dispatch('start');
    	}

    	// 컴포넌트가 마운트될 때 실행되는 함수
    	onMount(() => {
    		// 60ms 간격으로 글자를 하나씩 추가하는 타이머 설정
    		const interval = setInterval(
    			() => {
    				if (currentIndex < text.length) {
    					$$invalidate(0, displayText += text[currentIndex]);
    					currentIndex++;
    				} else {
    					$$invalidate(1, showingCursor = true);
    					clearInterval(interval);
    				}
    			},
    			60
    		);

    		// 컴포넌트가 언마운트될 때 타이머 정리
    		return () => clearInterval(interval);
    	});

    	const writable_props = [];

    	Object.keys($$props).forEach(key => {
    		if (!~writable_props.indexOf(key) && key.slice(0, 2) !== '$$' && key !== 'slot') console.warn(`<Welcome> was created with unknown prop '${key}'`);
    	});

    	$$self.$capture_state = () => ({
    		createEventDispatcher,
    		onMount,
    		dispatch,
    		text,
    		displayText,
    		currentIndex,
    		showingCursor,
    		handleStart
    	});

    	$$self.$inject_state = $$props => {
    		if ('text' in $$props) text = $$props.text;
    		if ('displayText' in $$props) $$invalidate(0, displayText = $$props.displayText);
    		if ('currentIndex' in $$props) currentIndex = $$props.currentIndex;
    		if ('showingCursor' in $$props) $$invalidate(1, showingCursor = $$props.showingCursor);
    	};

    	if ($$props && "$$inject" in $$props) {
    		$$self.$inject_state($$props.$$inject);
    	}

    	return [displayText, showingCursor, handleStart];
    }

    class Welcome extends SvelteComponentDev {
    	constructor(options) {
    		super(options);
    		init(this, options, instance$3, create_fragment$3, safe_not_equal, {});

    		dispatch_dev("SvelteRegisterComponent", {
    			component: this,
    			tagName: "Welcome",
    			options,
    			id: create_fragment$3.name
    		});
    	}
    }

    const API_URL = 'http://localhost:8000';  // API 서버 주소

    async function processVoiceInput(audioBlob, question, questionType) {
        if (!question || !questionType) {
            throw new Error('Question and questionType are required');
        }

        console.log('Processing voice input:', {
            blobSize: audioBlob.size,
            question,
            questionType
        });

        const formData = new FormData();
        formData.append('audio', audioBlob, 'voice.wav');
        formData.append('question', question);
        formData.append('question_type', questionType);

        try {
            console.log('Sending request to server...');
            const response = await fetch(`${API_URL}/process-voice`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            console.log('Server response:', result);

            if (!response.ok || !result.success) {
                throw new Error(result.error || 'Voice processing failed');
            }

            return result;
        } catch (error) {
            console.error('Error processing voice:', error);
            throw error;
        }
    }

    /* src\InfoInput.svelte generated by Svelte v3.59.2 */

    const { Error: Error_1, Object: Object_1$1, console: console_1 } = globals;
    const file$2 = "src\\InfoInput.svelte";

    function get_each_context$1(ctx, list, i) {
    	const child_ctx = ctx.slice();
    	child_ctx[31] = list[i];
    	return child_ctx;
    }

    // (299:22) {#if showingCursor}
    function create_if_block_5(ctx) {
    	let span;

    	const block = {
    		c: function create() {
    			span = element("span");
    			span.textContent = "_";
    			attr_dev(span, "class", "cursor svelte-17mial3");
    			add_location(span, file$2, 298, 41, 9264);
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, span, anchor);
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(span);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_if_block_5.name,
    		type: "if",
    		source: "(299:22) {#if showingCursor}",
    		ctx
    	});

    	return block;
    }

    // (302:3) {#if errorMessage}
    function create_if_block_4(ctx) {
    	let p;
    	let t;

    	const block = {
    		c: function create() {
    			p = element("p");
    			t = text(/*errorMessage*/ ctx[4]);
    			attr_dev(p, "class", "error svelte-17mial3");
    			add_location(p, file$2, 302, 5, 9349);
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, p, anchor);
    			append_dev(p, t);
    		},
    		p: function update(ctx, dirty) {
    			if (dirty[0] & /*errorMessage*/ 16) set_data_dev(t, /*errorMessage*/ ctx[4]);
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(p);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_if_block_4.name,
    		type: "if",
    		source: "(302:3) {#if errorMessage}",
    		ctx
    	});

    	return block;
    }

    // (345:3) {:else}
    function create_else_block(ctx) {
    	let input;
    	let input_step_value;
    	let input_required_value;
    	let typeAction_action;
    	let mounted;
    	let dispose;

    	const block = {
    		c: function create() {
    			input = element("input");
    			attr_dev(input, "step", input_step_value = /*steps*/ ctx[7][/*currentStep*/ ctx[0]].step);
    			input.required = input_required_value = /*steps*/ ctx[7][/*currentStep*/ ctx[0]].required;
    			attr_dev(input, "class", "svelte-17mial3");
    			add_location(input, file$2, 345, 5, 10697);
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, input, anchor);
    			set_input_value(input, /*userInfo*/ ctx[1][/*steps*/ ctx[7][/*currentStep*/ ctx[0]].field]);

    			if (!mounted) {
    				dispose = [
    					action_destroyer(typeAction_action = typeAction.call(null, input, /*steps*/ ctx[7][/*currentStep*/ ctx[0]].type)),
    					listen_dev(input, "input", /*input_input_handler*/ ctx[19]),
    					listen_dev(input, "input", /*handleInput*/ ctx[12], false, false, false, false)
    				];

    				mounted = true;
    			}
    		},
    		p: function update(ctx, dirty) {
    			if (dirty[0] & /*currentStep*/ 1 && input_step_value !== (input_step_value = /*steps*/ ctx[7][/*currentStep*/ ctx[0]].step)) {
    				attr_dev(input, "step", input_step_value);
    			}

    			if (dirty[0] & /*currentStep*/ 1 && input_required_value !== (input_required_value = /*steps*/ ctx[7][/*currentStep*/ ctx[0]].required)) {
    				prop_dev(input, "required", input_required_value);
    			}

    			if (typeAction_action && is_function(typeAction_action.update) && dirty[0] & /*currentStep*/ 1) typeAction_action.update.call(null, /*steps*/ ctx[7][/*currentStep*/ ctx[0]].type);

    			if (dirty[0] & /*userInfo, steps, currentStep*/ 131 && input.value !== /*userInfo*/ ctx[1][/*steps*/ ctx[7][/*currentStep*/ ctx[0]].field]) {
    				set_input_value(input, /*userInfo*/ ctx[1][/*steps*/ ctx[7][/*currentStep*/ ctx[0]].field]);
    			}
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(input);
    			mounted = false;
    			run_all(dispose);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_else_block.name,
    		type: "else",
    		source: "(345:3) {:else}",
    		ctx
    	});

    	return block;
    }

    // (324:53) 
    function create_if_block_3(ctx) {
    	let div;
    	let label0;
    	let t0;
    	let input0;
    	let input0_required_value;
    	let t1;
    	let label1;
    	let t2;
    	let input1;
    	let input1_required_value;
    	let mounted;
    	let dispose;

    	const block = {
    		c: function create() {
    			div = element("div");
    			label0 = element("label");
    			t0 = text("수축기 혈압:\r\n\t\t\t\t\t\t\t\t\t");
    			input0 = element("input");
    			t1 = space();
    			label1 = element("label");
    			t2 = text("이완기 혈압:\r\n\t\t\t\t\t\t\t\t\t");
    			input1 = element("input");
    			attr_dev(input0, "type", "number");
    			input0.required = input0_required_value = /*steps*/ ctx[7][/*currentStep*/ ctx[0]].required;
    			attr_dev(input0, "class", "svelte-17mial3");
    			add_location(input0, file$2, 327, 9, 10195);
    			attr_dev(label0, "class", "svelte-17mial3");
    			add_location(label0, file$2, 325, 7, 10159);
    			attr_dev(input1, "type", "number");
    			input1.required = input1_required_value = /*steps*/ ctx[7][/*currentStep*/ ctx[0]].required;
    			attr_dev(input1, "class", "svelte-17mial3");
    			add_location(input1, file$2, 336, 9, 10452);
    			attr_dev(label1, "class", "svelte-17mial3");
    			add_location(label1, file$2, 334, 7, 10416);
    			attr_dev(div, "class", "input-group svelte-17mial3");
    			add_location(div, file$2, 324, 5, 10125);
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, div, anchor);
    			append_dev(div, label0);
    			append_dev(label0, t0);
    			append_dev(label0, input0);
    			set_input_value(input0, /*userInfo*/ ctx[1].systolicBP);
    			append_dev(div, t1);
    			append_dev(div, label1);
    			append_dev(label1, t2);
    			append_dev(label1, input1);
    			set_input_value(input1, /*userInfo*/ ctx[1].diastolicBP);

    			if (!mounted) {
    				dispose = [
    					listen_dev(input0, "input", /*input0_input_handler*/ ctx[15]),
    					listen_dev(input0, "input", /*input_handler*/ ctx[16], false, false, false, false),
    					listen_dev(input1, "input", /*input1_input_handler*/ ctx[17]),
    					listen_dev(input1, "input", /*input_handler_1*/ ctx[18], false, false, false, false)
    				];

    				mounted = true;
    			}
    		},
    		p: function update(ctx, dirty) {
    			if (dirty[0] & /*currentStep*/ 1 && input0_required_value !== (input0_required_value = /*steps*/ ctx[7][/*currentStep*/ ctx[0]].required)) {
    				prop_dev(input0, "required", input0_required_value);
    			}

    			if (dirty[0] & /*userInfo*/ 2 && to_number(input0.value) !== /*userInfo*/ ctx[1].systolicBP) {
    				set_input_value(input0, /*userInfo*/ ctx[1].systolicBP);
    			}

    			if (dirty[0] & /*currentStep*/ 1 && input1_required_value !== (input1_required_value = /*steps*/ ctx[7][/*currentStep*/ ctx[0]].required)) {
    				prop_dev(input1, "required", input1_required_value);
    			}

    			if (dirty[0] & /*userInfo*/ 2 && to_number(input1.value) !== /*userInfo*/ ctx[1].diastolicBP) {
    				set_input_value(input1, /*userInfo*/ ctx[1].diastolicBP);
    			}
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(div);
    			mounted = false;
    			run_all(dispose);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_if_block_3.name,
    		type: "if",
    		source: "(324:53) ",
    		ctx
    	});

    	return block;
    }

    // (306:3) {#if steps[currentStep].type === 'select'}
    function create_if_block_2$1(ctx) {
    	let div;
    	let each_value = /*steps*/ ctx[7][/*currentStep*/ ctx[0]].options;
    	validate_each_argument(each_value);
    	let each_blocks = [];

    	for (let i = 0; i < each_value.length; i += 1) {
    		each_blocks[i] = create_each_block$1(get_each_context$1(ctx, each_value, i));
    	}

    	const block = {
    		c: function create() {
    			div = element("div");

    			for (let i = 0; i < each_blocks.length; i += 1) {
    				each_blocks[i].c();
    			}

    			attr_dev(div, "class", "button-group svelte-17mial3");
    			add_location(div, file$2, 306, 5, 9453);
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, div, anchor);

    			for (let i = 0; i < each_blocks.length; i += 1) {
    				if (each_blocks[i]) {
    					each_blocks[i].m(div, null);
    				}
    			}
    		},
    		p: function update(ctx, dirty) {
    			if (dirty[0] & /*userInfo, steps, currentStep, handleSelect*/ 2179) {
    				each_value = /*steps*/ ctx[7][/*currentStep*/ ctx[0]].options;
    				validate_each_argument(each_value);
    				let i;

    				for (i = 0; i < each_value.length; i += 1) {
    					const child_ctx = get_each_context$1(ctx, each_value, i);

    					if (each_blocks[i]) {
    						each_blocks[i].p(child_ctx, dirty);
    					} else {
    						each_blocks[i] = create_each_block$1(child_ctx);
    						each_blocks[i].c();
    						each_blocks[i].m(div, null);
    					}
    				}

    				for (; i < each_blocks.length; i += 1) {
    					each_blocks[i].d(1);
    				}

    				each_blocks.length = each_value.length;
    			}
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(div);
    			destroy_each(each_blocks, detaching);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_if_block_2$1.name,
    		type: "if",
    		source: "(306:3) {#if steps[currentStep].type === 'select'}",
    		ctx
    	});

    	return block;
    }

    // (308:7) {#each steps[currentStep].options as option}
    function create_each_block$1(ctx) {
    	let button;
    	let t0_value = /*option*/ ctx[31] + "";
    	let t0;
    	let t1;
    	let mounted;
    	let dispose;

    	function click_handler() {
    		return /*click_handler*/ ctx[14](/*option*/ ctx[31]);
    	}

    	const block = {
    		c: function create() {
    			button = element("button");
    			t0 = text(t0_value);
    			t1 = space();
    			attr_dev(button, "class", "svelte-17mial3");

    			toggle_class(button, "selected", /*userInfo*/ ctx[1][/*steps*/ ctx[7][/*currentStep*/ ctx[0]].field] === (/*steps*/ ctx[7][/*currentStep*/ ctx[0]].field === 'walking'
    			? Object.values({
    					'매우 많이 걷는다': 10000,
    					'꽤 많이 걷는다': 8000,
    					'보통 걷는다': 7000,
    					'조금 걷는다': 5600,
    					'거의 걷지 않는다': 3000
    				})[/*steps*/ ctx[7][/*currentStep*/ ctx[0]].options.indexOf(/*option*/ ctx[31])]
    			: /*option*/ ctx[31]));

    			add_location(button, file$2, 308, 9, 9543);
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, button, anchor);
    			append_dev(button, t0);
    			append_dev(button, t1);

    			if (!mounted) {
    				dispose = listen_dev(button, "click", click_handler, false, false, false, false);
    				mounted = true;
    			}
    		},
    		p: function update(new_ctx, dirty) {
    			ctx = new_ctx;
    			if (dirty[0] & /*currentStep*/ 1 && t0_value !== (t0_value = /*option*/ ctx[31] + "")) set_data_dev(t0, t0_value);

    			if (dirty[0] & /*userInfo, steps, currentStep*/ 131) {
    				toggle_class(button, "selected", /*userInfo*/ ctx[1][/*steps*/ ctx[7][/*currentStep*/ ctx[0]].field] === (/*steps*/ ctx[7][/*currentStep*/ ctx[0]].field === 'walking'
    				? Object.values({
    						'매우 많이 걷는다': 10000,
    						'꽤 많이 걷는다': 8000,
    						'보통 걷는다': 7000,
    						'조금 걷는다': 5600,
    						'거의 걷지 않는다': 3000
    					})[/*steps*/ ctx[7][/*currentStep*/ ctx[0]].options.indexOf(/*option*/ ctx[31])]
    				: /*option*/ ctx[31]));
    			}
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(button);
    			mounted = false;
    			dispose();
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_each_block$1.name,
    		type: "each",
    		source: "(308:7) {#each steps[currentStep].options as option}",
    		ctx
    	});

    	return block;
    }

    // (357:4) {#if recordingStatus}
    function create_if_block_1$1(ctx) {
    	let div;
    	let t;

    	const block = {
    		c: function create() {
    			div = element("div");
    			t = text(/*recordingStatus*/ ctx[6]);
    			attr_dev(div, "class", "recording-status svelte-17mial3");
    			add_location(div, file$2, 357, 5, 11046);
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, div, anchor);
    			append_dev(div, t);
    		},
    		p: function update(ctx, dirty) {
    			if (dirty[0] & /*recordingStatus*/ 64) set_data_dev(t, /*recordingStatus*/ ctx[6]);
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(div);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_if_block_1$1.name,
    		type: "if",
    		source: "(357:4) {#if recordingStatus}",
    		ctx
    	});

    	return block;
    }

    // (374:5) {#if !steps[currentStep].required}
    function create_if_block$1(ctx) {
    	let button;
    	let mounted;
    	let dispose;

    	const block = {
    		c: function create() {
    			button = element("button");
    			button.textContent = "건너뛰기";
    			attr_dev(button, "class", "svelte-17mial3");
    			add_location(button, file$2, 374, 7, 11507);
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, button, anchor);

    			if (!mounted) {
    				dispose = listen_dev(button, "click", /*handleSkip*/ ctx[10], false, false, false, false);
    				mounted = true;
    			}
    		},
    		p: noop,
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(button);
    			mounted = false;
    			dispose();
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_if_block$1.name,
    		type: "if",
    		source: "(374:5) {#if !steps[currentStep].required}",
    		ctx
    	});

    	return block;
    }

    function create_fragment$2(ctx) {
    	let div4;
    	let div3;
    	let div0;
    	let h2;
    	let t0;
    	let t1;
    	let t2;
    	let show_if;
    	let t3;
    	let div1;
    	let t4;
    	let button0;
    	let span;
    	let t6;

    	let t7_value = (/*isRecording*/ ctx[5]
    	? '녹음 중지하기 (Space)'
    	: '음성으로 답변하기 (Space)') + "";

    	let t7;
    	let t8;
    	let div2;
    	let button1;
    	let t10;
    	let t11;
    	let button2;

    	let t12_value = (/*currentStep*/ ctx[0] === /*steps*/ ctx[7].length - 1
    	? '확인'
    	: '다음') + "";

    	let t12;
    	let mounted;
    	let dispose;
    	let if_block0 = /*showingCursor*/ ctx[3] && create_if_block_5(ctx);
    	let if_block1 = /*errorMessage*/ ctx[4] && create_if_block_4(ctx);

    	function select_block_type(ctx, dirty) {
    		if (dirty[0] & /*currentStep*/ 1) show_if = null;
    		if (/*steps*/ ctx[7][/*currentStep*/ ctx[0]].type === 'select') return create_if_block_2$1;
    		if (show_if == null) show_if = !!Array.isArray(/*steps*/ ctx[7][/*currentStep*/ ctx[0]].field);
    		if (show_if) return create_if_block_3;
    		return create_else_block;
    	}

    	let current_block_type = select_block_type(ctx, [-1, -1]);
    	let if_block2 = current_block_type(ctx);
    	let if_block3 = /*recordingStatus*/ ctx[6] && create_if_block_1$1(ctx);
    	let if_block4 = !/*steps*/ ctx[7][/*currentStep*/ ctx[0]].required && create_if_block$1(ctx);

    	const block = {
    		c: function create() {
    			div4 = element("div");
    			div3 = element("div");
    			div0 = element("div");
    			h2 = element("h2");
    			t0 = text(/*displayText*/ ctx[2]);
    			if (if_block0) if_block0.c();
    			t1 = space();
    			if (if_block1) if_block1.c();
    			t2 = space();
    			if_block2.c();
    			t3 = space();
    			div1 = element("div");
    			if (if_block3) if_block3.c();
    			t4 = space();
    			button0 = element("button");
    			span = element("span");
    			span.textContent = "🎤";
    			t6 = space();
    			t7 = text(t7_value);
    			t8 = space();
    			div2 = element("div");
    			button1 = element("button");
    			button1.textContent = "뒤로가기";
    			t10 = space();
    			if (if_block4) if_block4.c();
    			t11 = space();
    			button2 = element("button");
    			t12 = text(t12_value);
    			attr_dev(h2, "class", "svelte-17mial3");
    			add_location(h2, file$2, 298, 5, 9228);
    			attr_dev(div0, "class", "question-container svelte-17mial3");
    			add_location(div0, file$2, 297, 3, 9189);
    			attr_dev(span, "class", "mic-icon svelte-17mial3");
    			add_location(span, file$2, 366, 5, 11256);
    			attr_dev(button0, "class", "voice-input-button svelte-17mial3");
    			toggle_class(button0, "recording", /*isRecording*/ ctx[5]);
    			add_location(button0, file$2, 361, 4, 11131);
    			attr_dev(div1, "class", "voice-input-container svelte-17mial3");
    			add_location(div1, file$2, 355, 3, 10977);
    			attr_dev(button1, "class", "svelte-17mial3");
    			add_location(button1, file$2, 372, 5, 11414);
    			attr_dev(button2, "class", "svelte-17mial3");
    			add_location(button2, file$2, 376, 5, 11569);
    			attr_dev(div2, "class", "navigation svelte-17mial3");
    			add_location(div2, file$2, 371, 3, 11383);
    			attr_dev(div3, "class", "info-input svelte-17mial3");
    			add_location(div3, file$2, 296, 1, 9160);
    			attr_dev(div4, "class", "background svelte-17mial3");
    			add_location(div4, file$2, 295, 0, 9133);
    		},
    		l: function claim(nodes) {
    			throw new Error_1("options.hydrate only works if the component was compiled with the `hydratable: true` option");
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, div4, anchor);
    			append_dev(div4, div3);
    			append_dev(div3, div0);
    			append_dev(div0, h2);
    			append_dev(h2, t0);
    			if (if_block0) if_block0.m(h2, null);
    			append_dev(div3, t1);
    			if (if_block1) if_block1.m(div3, null);
    			append_dev(div3, t2);
    			if_block2.m(div3, null);
    			append_dev(div3, t3);
    			append_dev(div3, div1);
    			if (if_block3) if_block3.m(div1, null);
    			append_dev(div1, t4);
    			append_dev(div1, button0);
    			append_dev(button0, span);
    			append_dev(button0, t6);
    			append_dev(button0, t7);
    			append_dev(div3, t8);
    			append_dev(div3, div2);
    			append_dev(div2, button1);
    			append_dev(div2, t10);
    			if (if_block4) if_block4.m(div2, null);
    			append_dev(div2, t11);
    			append_dev(div2, button2);
    			append_dev(button2, t12);

    			if (!mounted) {
    				dispose = [
    					listen_dev(button0, "click", /*startVoiceInput*/ ctx[13], false, false, false, false),
    					listen_dev(button1, "click", /*handleBack*/ ctx[9], false, false, false, false),
    					listen_dev(button2, "click", /*handleNext*/ ctx[8], false, false, false, false)
    				];

    				mounted = true;
    			}
    		},
    		p: function update(ctx, dirty) {
    			if (dirty[0] & /*displayText*/ 4) set_data_dev(t0, /*displayText*/ ctx[2]);

    			if (/*showingCursor*/ ctx[3]) {
    				if (if_block0) ; else {
    					if_block0 = create_if_block_5(ctx);
    					if_block0.c();
    					if_block0.m(h2, null);
    				}
    			} else if (if_block0) {
    				if_block0.d(1);
    				if_block0 = null;
    			}

    			if (/*errorMessage*/ ctx[4]) {
    				if (if_block1) {
    					if_block1.p(ctx, dirty);
    				} else {
    					if_block1 = create_if_block_4(ctx);
    					if_block1.c();
    					if_block1.m(div3, t2);
    				}
    			} else if (if_block1) {
    				if_block1.d(1);
    				if_block1 = null;
    			}

    			if (current_block_type === (current_block_type = select_block_type(ctx, dirty)) && if_block2) {
    				if_block2.p(ctx, dirty);
    			} else {
    				if_block2.d(1);
    				if_block2 = current_block_type(ctx);

    				if (if_block2) {
    					if_block2.c();
    					if_block2.m(div3, t3);
    				}
    			}

    			if (/*recordingStatus*/ ctx[6]) {
    				if (if_block3) {
    					if_block3.p(ctx, dirty);
    				} else {
    					if_block3 = create_if_block_1$1(ctx);
    					if_block3.c();
    					if_block3.m(div1, t4);
    				}
    			} else if (if_block3) {
    				if_block3.d(1);
    				if_block3 = null;
    			}

    			if (dirty[0] & /*isRecording*/ 32 && t7_value !== (t7_value = (/*isRecording*/ ctx[5]
    			? '녹음 중지하기 (Space)'
    			: '음성으로 답변하기 (Space)') + "")) set_data_dev(t7, t7_value);

    			if (dirty[0] & /*isRecording*/ 32) {
    				toggle_class(button0, "recording", /*isRecording*/ ctx[5]);
    			}

    			if (!/*steps*/ ctx[7][/*currentStep*/ ctx[0]].required) {
    				if (if_block4) {
    					if_block4.p(ctx, dirty);
    				} else {
    					if_block4 = create_if_block$1(ctx);
    					if_block4.c();
    					if_block4.m(div2, t11);
    				}
    			} else if (if_block4) {
    				if_block4.d(1);
    				if_block4 = null;
    			}

    			if (dirty[0] & /*currentStep*/ 1 && t12_value !== (t12_value = (/*currentStep*/ ctx[0] === /*steps*/ ctx[7].length - 1
    			? '확인'
    			: '다음') + "")) set_data_dev(t12, t12_value);
    		},
    		i: noop,
    		o: noop,
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(div4);
    			if (if_block0) if_block0.d();
    			if (if_block1) if_block1.d();
    			if_block2.d();
    			if (if_block3) if_block3.d();
    			if (if_block4) if_block4.d();
    			mounted = false;
    			run_all(dispose);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_fragment$2.name,
    		type: "component",
    		source: "",
    		ctx
    	});

    	return block;
    }

    function typeAction(node, type) {
    	node.type = type;

    	return {
    		update(newType) {
    			node.type = newType;
    		}
    	};
    }

    function instance$2($$self, $$props, $$invalidate) {
    	let { $$slots: slots = {}, $$scope } = $$props;
    	validate_slots('InfoInput', slots, []);
    	const dispatch = createEventDispatcher();
    	let currentStep = 0;

    	let userInfo = {
    		name: '',
    		age: '',
    		sex: '',
    		weight: '',
    		height: '',
    		sleepTime: '',
    		drink: '',
    		smoke: '',
    		fatigue: '',
    		systolicBP: '',
    		diastolicBP: '',
    		heartRate: '',
    		walking: '',
    		cholesterol: ''
    	};

    	// 타이핑 효과를 위한 변수들
    	let displayText = "";

    	let currentIndex = 0;
    	let showingCursor = false;
    	let errorMessage = '';

    	const steps = [
    		{
    			field: 'name',
    			label: '성함이 어떻게 되시나요?',
    			type: 'text',
    			required: true
    		},
    		{
    			field: 'age',
    			label: '연세가 어떻게 되시나요?',
    			type: 'number',
    			required: true
    		},
    		{
    			field: 'sex',
    			label: '성별을 선택해 주세요',
    			type: 'select',
    			options: ['남자', '여자'],
    			required: true
    		},
    		{
    			field: 'weight',
    			label: '몸무게는 몇 kg이신가요?',
    			type: 'number',
    			step: '0.1',
    			required: true
    		},
    		{
    			field: 'height',
    			label: '키는 몇 cm이신가요?',
    			type: 'number',
    			step: '0.1',
    			required: true
    		},
    		{
    			field: 'sleepTime',
    			label: '하루에 몇 시간 주무시나요?',
    			type: 'number',
    			step: '0.5',
    			required: true
    		},
    		{
    			field: 'drink',
    			label: '술을 드시나요?',
    			type: 'select',
    			options: ['예', '아니오'],
    			required: true
    		},
    		{
    			field: 'smoke',
    			label: '담배를 피우시나요?',
    			type: 'select',
    			options: ['예', '아니오'],
    			required: true
    		},
    		{
    			field: 'fatigue',
    			label: '평소에 피로감을 느끼시나요?',
    			type: 'select',
    			options: ['예', '아니오'],
    			required: true
    		},
    		{
    			field: ['systolicBP', 'diastolicBP'],
    			label: '혈압은 어떻게 되시나요?',
    			type: 'number',
    			required: false
    		},
    		{
    			field: 'heartRate',
    			label: '심장박동수는 어떻게 되시나요?',
    			type: 'number',
    			required: false
    		},
    		{
    			field: 'walking',
    			label: '평소에 걷기 운동을 얼마나 하시나요?',
    			type: 'select',
    			options: ['매우 많이 걷는다', '꽤 많이 걷는다', '보통 걷는다', '조금 걷는다', '거의 걷지 않는다'],
    			required: false
    		},
    		{
    			field: 'cholesterol',
    			label: '콜레스테롤이 높다고 들어보셨나요?',
    			type: 'select',
    			options: ['예', '아니오'],
    			required: false
    		}
    	];

    	onMount(() => {
    		startTyping();

    		// 키보드 이벤트 리스너 추가
    		window.addEventListener('keydown', handleKeydown);

    		// 컴포넌트 제거 시 이벤트 리스너 정리
    		return () => {
    			window.removeEventListener('keydown', handleKeydown);
    		};
    	});

    	function clearTypingEffect() {
    		$$invalidate(2, displayText = "");
    		currentIndex = 0;
    		$$invalidate(3, showingCursor = false);
    	}

    	function startTyping() {
    		const text = steps[currentStep].label;

    		const interval = setInterval(
    			() => {
    				if (currentIndex < text.length) {
    					$$invalidate(2, displayText = text.substring(0, currentIndex + 1)); // 문자열 슬라이싱 사용
    					currentIndex++;
    				} else {
    					$$invalidate(3, showingCursor = true);
    					clearInterval(interval);
    				}
    			},
    			60
    		);

    		return () => clearInterval(interval); // 클린업 함수
    	}

    	function handleNext() {
    		if (isValidInput()) {
    			$$invalidate(4, errorMessage = '');

    			if (currentStep < steps.length - 1) {
    				$$invalidate(0, currentStep++, currentStep);
    			} else {
    				dispatch('finish', userInfo);
    			}
    		}
    	}

    	function handleBack() {
    		$$invalidate(4, errorMessage = '');

    		if (currentStep > 0) {
    			$$invalidate(0, currentStep--, currentStep);
    		} else {
    			dispatch('goToWelcome');
    		}
    	}

    	function handleSkip() {
    		$$invalidate(4, errorMessage = '');

    		if (!steps[currentStep].required) {
    			if (Array.isArray(steps[currentStep].field)) {
    				steps[currentStep].field.forEach(field => {
    					$$invalidate(1, userInfo[field] = null, userInfo);
    				});
    			} else {
    				$$invalidate(1, userInfo[steps[currentStep].field] = null, userInfo);
    			}

    			if (currentStep < steps.length - 1) {
    				$$invalidate(0, currentStep++, currentStep);
    			} else {
    				dispatch('finish', userInfo);
    			}
    		}
    	}

    	function isValidInput() {
    		const currentStepInfo = steps[currentStep];

    		if (currentStepInfo.field === 'walking' || currentStepInfo.field === 'cholesterol') {
    			return true;
    		}

    		if (Array.isArray(currentStepInfo.field)) {
    			const systolic = userInfo.systolicBP;
    			const diastolic = userInfo.diastolicBP;

    			if (systolic && !diastolic || !systolic && diastolic) {
    				$$invalidate(4, errorMessage = '수축기 혈압과 이완기 혈압을 모두 입력해주세요.');
    				return false;
    			}

    			return true;
    		} else {
    			const value = userInfo[currentStepInfo.field];

    			if (currentStepInfo.required && (value === '' || value === null || value === undefined)) {
    				return false;
    			}

    			if (currentStepInfo.field === 'name') {
    				if (!(/^[가-힣a-zA-Z\s]+$/).test(value)) {
    					$$invalidate(4, errorMessage = '이름은 문자만 입력 가능합니다.');
    					return false;
    				}
    			}

    			if (currentStepInfo.type === 'number') {
    				const numValue = parseFloat(value);

    				if (isNaN(numValue)) {
    					return false;
    				}

    				if (currentStepInfo.step) {
    					const step = parseFloat(currentStepInfo.step);
    					const remainder = numValue / step % 1;

    					if (remainder !== 0 && Math.abs(remainder - 1) > Number.EPSILON) {
    						return false;
    					}
    				}
    			}

    			if (currentStepInfo.type === 'select') {
    				return currentStepInfo.options.includes(value);
    			}
    		}

    		return true;
    	}

    	function handleSelect(option) {
    		const currentField = steps[currentStep].field;

    		if (currentField === 'walking') {
    			const walkingValues = {
    				'매우 많이 걷는다': 10000,
    				'꽤 많이 걷는다': 8000,
    				'보통 걷는다': 7000,
    				'조금 걷는다': 5600,
    				'거의 걷지 않는다': 3000
    			};

    			$$invalidate(1, userInfo[currentField] = walkingValues[option], userInfo);
    		} else {
    			$$invalidate(1, userInfo[currentField] = option, userInfo);
    		}

    		$$invalidate(1, userInfo = { ...userInfo });
    	}

    	function handleInput(event) {
    		if (steps[currentStep].field === 'name') {
    			event.target.value = event.target.value.replace(/[^가-힣a-zA-Z\s]/g, '');
    		}
    	}

    	let isRecording = false;
    	let mediaRecorder;
    	let audioChunks = [];
    	let recordingStatus = '';
    	let recordingTime = 0;
    	let recordingTimer;

    	function updateRecordingTime() {
    		recordingTime++;
    		$$invalidate(6, recordingStatus = `녹음 중... (${recordingTime}초)`);
    	}

    	async function startVoiceInput() {
    		if (isRecording) {
    			clearInterval(recordingTimer);
    			$$invalidate(6, recordingStatus = '녹음 처리 중...');
    			mediaRecorder.stop();
    			$$invalidate(5, isRecording = false);
    			return;
    		}

    		try {
    			const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    			$$invalidate(5, isRecording = true);
    			audioChunks = [];
    			recordingTime = 0;
    			$$invalidate(6, recordingStatus = '녹음 시작...');
    			$$invalidate(4, errorMessage = '');
    			mediaRecorder = new MediaRecorder(stream);

    			mediaRecorder.ondataavailable = event => {
    				audioChunks.push(event.data);
    			};

    			mediaRecorder.onstop = async () => {
    				try {
    					const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    					const currentStepInfo = steps[currentStep];

    					if (!currentStepInfo) {
    						throw new Error('현재 단계 정보를 찾을 수 없습니다.');
    					}

    					$$invalidate(6, recordingStatus = '음성 처리 중...');
    					const result = await processVoiceInput(audioBlob, currentStepInfo.label, currentStepInfo.field);

    					if (result.success && result.processed_answer) {
    						$$invalidate(6, recordingStatus = `인식된 답변: ${result.raw_text}`);
    						$$invalidate(1, userInfo[currentStepInfo.field] = result.processed_answer, userInfo);

    						setTimeout(
    							() => {
    								if (isValidInput()) {
    									handleNext();
    								}

    								$$invalidate(6, recordingStatus = '');
    							},
    							2000
    						);
    					} else {
    						throw new Error(result.error || '음성 처리에 실패했습니다.');
    					}
    				} catch(error) {
    					console.error('Voice processing error:', error);
    					$$invalidate(6, recordingStatus = '');
    					$$invalidate(4, errorMessage = error.message || '음성 처리 중 오류가 발생했습니다.');
    				} finally {
    					stream.getTracks().forEach(track => track.stop());
    				}
    			};

    			mediaRecorder.start();
    			recordingTimer = setInterval(updateRecordingTime, 1000);
    		} catch(error) {
    			console.error('Error accessing microphone:', error);
    			$$invalidate(6, recordingStatus = '');
    			$$invalidate(4, errorMessage = '마이크 접근에 실패했습니다.');
    		}
    	}

    	// 키보드 이벤트 핸들러 추가
    	function handleKeydown(event) {
    		if (event.code === 'Space') {
    			event.preventDefault(); // 스페이스바의 기본 동작 방지
    			startVoiceInput();
    		}
    	}

    	const writable_props = [];

    	Object_1$1.keys($$props).forEach(key => {
    		if (!~writable_props.indexOf(key) && key.slice(0, 2) !== '$$' && key !== 'slot') console_1.warn(`<InfoInput> was created with unknown prop '${key}'`);
    	});

    	const click_handler = option => handleSelect(option);

    	function input0_input_handler() {
    		userInfo.systolicBP = to_number(this.value);
    		$$invalidate(1, userInfo);
    	}

    	const input_handler = () => $$invalidate(1, userInfo = { ...userInfo });

    	function input1_input_handler() {
    		userInfo.diastolicBP = to_number(this.value);
    		$$invalidate(1, userInfo);
    	}

    	const input_handler_1 = () => $$invalidate(1, userInfo = { ...userInfo });

    	function input_input_handler() {
    		userInfo[steps[currentStep].field] = this.value;
    		$$invalidate(1, userInfo);
    	}

    	$$self.$capture_state = () => ({
    		createEventDispatcher,
    		onMount,
    		processVoiceInput,
    		dispatch,
    		currentStep,
    		userInfo,
    		displayText,
    		currentIndex,
    		showingCursor,
    		errorMessage,
    		steps,
    		clearTypingEffect,
    		startTyping,
    		handleNext,
    		handleBack,
    		handleSkip,
    		isValidInput,
    		typeAction,
    		handleSelect,
    		handleInput,
    		isRecording,
    		mediaRecorder,
    		audioChunks,
    		recordingStatus,
    		recordingTime,
    		recordingTimer,
    		updateRecordingTime,
    		startVoiceInput,
    		handleKeydown
    	});

    	$$self.$inject_state = $$props => {
    		if ('currentStep' in $$props) $$invalidate(0, currentStep = $$props.currentStep);
    		if ('userInfo' in $$props) $$invalidate(1, userInfo = $$props.userInfo);
    		if ('displayText' in $$props) $$invalidate(2, displayText = $$props.displayText);
    		if ('currentIndex' in $$props) currentIndex = $$props.currentIndex;
    		if ('showingCursor' in $$props) $$invalidate(3, showingCursor = $$props.showingCursor);
    		if ('errorMessage' in $$props) $$invalidate(4, errorMessage = $$props.errorMessage);
    		if ('isRecording' in $$props) $$invalidate(5, isRecording = $$props.isRecording);
    		if ('mediaRecorder' in $$props) mediaRecorder = $$props.mediaRecorder;
    		if ('audioChunks' in $$props) audioChunks = $$props.audioChunks;
    		if ('recordingStatus' in $$props) $$invalidate(6, recordingStatus = $$props.recordingStatus);
    		if ('recordingTime' in $$props) recordingTime = $$props.recordingTime;
    		if ('recordingTimer' in $$props) recordingTimer = $$props.recordingTimer;
    	};

    	if ($$props && "$$inject" in $$props) {
    		$$self.$inject_state($$props.$$inject);
    	}

    	$$self.$$.update = () => {
    		if ($$self.$$.dirty[0] & /*currentStep*/ 1) {
    			// steps 배열이나 currentStep이 변경될 때마다 타이핑 효과 재시작
    			if (steps[currentStep]) {
    				clearTypingEffect(); // 타이핑 효과 초기화
    				startTyping();
    			}
    		}
    	};

    	return [
    		currentStep,
    		userInfo,
    		displayText,
    		showingCursor,
    		errorMessage,
    		isRecording,
    		recordingStatus,
    		steps,
    		handleNext,
    		handleBack,
    		handleSkip,
    		handleSelect,
    		handleInput,
    		startVoiceInput,
    		click_handler,
    		input0_input_handler,
    		input_handler,
    		input1_input_handler,
    		input_handler_1,
    		input_input_handler
    	];
    }

    class InfoInput extends SvelteComponentDev {
    	constructor(options) {
    		super(options);
    		init(this, options, instance$2, create_fragment$2, safe_not_equal, {}, null, [-1, -1]);

    		dispatch_dev("SvelteRegisterComponent", {
    			component: this,
    			tagName: "InfoInput",
    			options,
    			id: create_fragment$2.name
    		});
    	}
    }

    /* src\InfoConfirm.svelte generated by Svelte v3.59.2 */

    const { Object: Object_1 } = globals;
    const file$1 = "src\\InfoConfirm.svelte";

    function get_each_context(ctx, list, i) {
    	const child_ctx = ctx.slice();
    	child_ctx[4] = list[i][0];
    	child_ctx[5] = list[i][1];
    	return child_ctx;
    }

    // (69:6) {#each Object.entries(userInfo) as [key, value]}
    function create_each_block(ctx) {
    	let div;
    	let span0;
    	let t0_value = formatLabel(/*key*/ ctx[4]) + "";
    	let t0;
    	let t1;
    	let t2;
    	let span1;
    	let t3_value = formatValue(/*key*/ ctx[4], /*value*/ ctx[5]) + "";
    	let t3;
    	let t4;

    	const block = {
    		c: function create() {
    			div = element("div");
    			span0 = element("span");
    			t0 = text(t0_value);
    			t1 = text(":");
    			t2 = space();
    			span1 = element("span");
    			t3 = text(t3_value);
    			t4 = space();
    			attr_dev(span0, "class", "label svelte-m6opzu");
    			add_location(span0, file$1, 70, 14, 1816);
    			attr_dev(span1, "class", "value");
    			add_location(span1, file$1, 71, 14, 1878);
    			attr_dev(div, "class", "info-item svelte-m6opzu");
    			add_location(div, file$1, 69, 10, 1777);
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, div, anchor);
    			append_dev(div, span0);
    			append_dev(span0, t0);
    			append_dev(span0, t1);
    			append_dev(div, t2);
    			append_dev(div, span1);
    			append_dev(span1, t3);
    			append_dev(div, t4);
    		},
    		p: function update(ctx, dirty) {
    			if (dirty & /*userInfo*/ 1 && t0_value !== (t0_value = formatLabel(/*key*/ ctx[4]) + "")) set_data_dev(t0, t0_value);
    			if (dirty & /*userInfo*/ 1 && t3_value !== (t3_value = formatValue(/*key*/ ctx[4], /*value*/ ctx[5]) + "")) set_data_dev(t3, t3_value);
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(div);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_each_block.name,
    		type: "each",
    		source: "(69:6) {#each Object.entries(userInfo) as [key, value]}",
    		ctx
    	});

    	return block;
    }

    function create_fragment$1(ctx) {
    	let div2;
    	let h2;
    	let t1;
    	let div0;
    	let t2;
    	let div1;
    	let button0;
    	let t4;
    	let button1;
    	let mounted;
    	let dispose;
    	let each_value = Object.entries(/*userInfo*/ ctx[0]);
    	validate_each_argument(each_value);
    	let each_blocks = [];

    	for (let i = 0; i < each_value.length; i += 1) {
    		each_blocks[i] = create_each_block(get_each_context(ctx, each_value, i));
    	}

    	const block = {
    		c: function create() {
    			div2 = element("div");
    			h2 = element("h2");
    			h2.textContent = "입력하신 정보가 맞나요?";
    			t1 = space();
    			div0 = element("div");

    			for (let i = 0; i < each_blocks.length; i += 1) {
    				each_blocks[i].c();
    			}

    			t2 = space();
    			div1 = element("div");
    			button0 = element("button");
    			button0.textContent = "돌아가기";
    			t4 = space();
    			button1 = element("button");
    			button1.textContent = "확인";
    			attr_dev(h2, "class", "svelte-m6opzu");
    			add_location(h2, file$1, 65, 2, 1656);
    			attr_dev(div0, "class", "info-list svelte-m6opzu");
    			add_location(div0, file$1, 67, 2, 1686);
    			add_location(button0, file$1, 77, 6, 2011);
    			add_location(button1, file$1, 78, 6, 2062);
    			attr_dev(div1, "class", "navigation svelte-m6opzu");
    			add_location(div1, file$1, 76, 2, 1979);
    			attr_dev(div2, "class", "info-confirm svelte-m6opzu");
    			add_location(div2, file$1, 64, 0, 1626);
    		},
    		l: function claim(nodes) {
    			throw new Error("options.hydrate only works if the component was compiled with the `hydratable: true` option");
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, div2, anchor);
    			append_dev(div2, h2);
    			append_dev(div2, t1);
    			append_dev(div2, div0);

    			for (let i = 0; i < each_blocks.length; i += 1) {
    				if (each_blocks[i]) {
    					each_blocks[i].m(div0, null);
    				}
    			}

    			append_dev(div2, t2);
    			append_dev(div2, div1);
    			append_dev(div1, button0);
    			append_dev(div1, t4);
    			append_dev(div1, button1);

    			if (!mounted) {
    				dispose = [
    					listen_dev(button0, "click", /*handleBack*/ ctx[1], false, false, false, false),
    					listen_dev(button1, "click", /*click_handler*/ ctx[2], false, false, false, false)
    				];

    				mounted = true;
    			}
    		},
    		p: function update(ctx, [dirty]) {
    			if (dirty & /*formatValue, Object, userInfo, formatLabel*/ 1) {
    				each_value = Object.entries(/*userInfo*/ ctx[0]);
    				validate_each_argument(each_value);
    				let i;

    				for (i = 0; i < each_value.length; i += 1) {
    					const child_ctx = get_each_context(ctx, each_value, i);

    					if (each_blocks[i]) {
    						each_blocks[i].p(child_ctx, dirty);
    					} else {
    						each_blocks[i] = create_each_block(child_ctx);
    						each_blocks[i].c();
    						each_blocks[i].m(div0, null);
    					}
    				}

    				for (; i < each_blocks.length; i += 1) {
    					each_blocks[i].d(1);
    				}

    				each_blocks.length = each_value.length;
    			}
    		},
    		i: noop,
    		o: noop,
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(div2);
    			destroy_each(each_blocks, detaching);
    			mounted = false;
    			run_all(dispose);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_fragment$1.name,
    		type: "component",
    		source: "",
    		ctx
    	});

    	return block;
    }

    function formatLabel(key) {
    	const labels = {
    		name: '성함',
    		age: '연령',
    		sex: '성별',
    		weight: '몸무게',
    		height: '키',
    		sleepTime: '하루 수면시간',
    		drink: '음주 여부',
    		smoke: '흡연 여부',
    		fatigue: '피로 여부',
    		systolicBP: '수축기 혈압',
    		diastolicBP: '이완기 혈압',
    		heartRate: '심박수',
    		walking: '하루 걸음 수',
    		cholesterol: '콜레스테롤 과다 여부'
    	};

    	return labels[key] || key;
    }

    function formatValue(key, value) {
    	if (value === null || value === undefined || value === '') {
    		return '미입력';
    	}

    	if (key === 'sex') {
    		return value === '남자' ? '남자' : '여자';
    	}

    	if (['drink', 'smoke', 'fatigue', 'cholesterol'].includes(key)) {
    		return value === '예' ? '예' : '아니오';
    	}

    	if (key === 'weight') {
    		return `${value} kg`;
    	}

    	if (key === 'height') {
    		return `${value} cm`;
    	}

    	if (key === 'sleepTime') {
    		return `${value} 시간`;
    	}

    	if (key === 'walking') {
    		const walkingLabels = {
    			10000: '매우 많이 걷는다',
    			8000: '꽤 많이 걷는다',
    			7000: '보통 걷는다',
    			5600: '조금 걷는다',
    			3000: '거의 걷지 않는다'
    		};

    		return `${walkingLabels[value]} (${value} 걸음)`;
    	}

    	return value;
    }

    function instance$1($$self, $$props, $$invalidate) {
    	let { $$slots: slots = {}, $$scope } = $$props;
    	validate_slots('InfoConfirm', slots, []);
    	let { userInfo } = $$props;
    	const dispatch = createEventDispatcher();

    	function handleBack() {
    		dispatch('back');
    	}

    	$$self.$$.on_mount.push(function () {
    		if (userInfo === undefined && !('userInfo' in $$props || $$self.$$.bound[$$self.$$.props['userInfo']])) {
    			console.warn("<InfoConfirm> was created without expected prop 'userInfo'");
    		}
    	});

    	const writable_props = ['userInfo'];

    	Object_1.keys($$props).forEach(key => {
    		if (!~writable_props.indexOf(key) && key.slice(0, 2) !== '$$' && key !== 'slot') console.warn(`<InfoConfirm> was created with unknown prop '${key}'`);
    	});

    	const click_handler = () => alert('정보가 저장되었습니다.');

    	$$self.$$set = $$props => {
    		if ('userInfo' in $$props) $$invalidate(0, userInfo = $$props.userInfo);
    	};

    	$$self.$capture_state = () => ({
    		createEventDispatcher,
    		userInfo,
    		dispatch,
    		handleBack,
    		formatLabel,
    		formatValue
    	});

    	$$self.$inject_state = $$props => {
    		if ('userInfo' in $$props) $$invalidate(0, userInfo = $$props.userInfo);
    	};

    	if ($$props && "$$inject" in $$props) {
    		$$self.$inject_state($$props.$$inject);
    	}

    	return [userInfo, handleBack, click_handler];
    }

    class InfoConfirm extends SvelteComponentDev {
    	constructor(options) {
    		super(options);
    		init(this, options, instance$1, create_fragment$1, safe_not_equal, { userInfo: 0 });

    		dispatch_dev("SvelteRegisterComponent", {
    			component: this,
    			tagName: "InfoConfirm",
    			options,
    			id: create_fragment$1.name
    		});
    	}

    	get userInfo() {
    		throw new Error("<InfoConfirm>: Props cannot be read directly from the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}

    	set userInfo(value) {
    		throw new Error("<InfoConfirm>: Props cannot be set directly on the component instance unless compiling with 'accessors: true' or '<svelte:options accessors/>'");
    	}
    }

    /* src\App.svelte generated by Svelte v3.59.2 */
    const file = "src\\App.svelte";

    // (34:41) 
    function create_if_block_2(ctx) {
    	let infoconfirm;
    	let current;

    	infoconfirm = new InfoConfirm({
    			props: { userInfo: /*userInfo*/ ctx[1] },
    			$$inline: true
    		});

    	infoconfirm.$on("back", /*goBack*/ ctx[4]);

    	const block = {
    		c: function create() {
    			create_component(infoconfirm.$$.fragment);
    		},
    		m: function mount(target, anchor) {
    			mount_component(infoconfirm, target, anchor);
    			current = true;
    		},
    		p: function update(ctx, dirty) {
    			const infoconfirm_changes = {};
    			if (dirty & /*userInfo*/ 2) infoconfirm_changes.userInfo = /*userInfo*/ ctx[1];
    			infoconfirm.$set(infoconfirm_changes);
    		},
    		i: function intro(local) {
    			if (current) return;
    			transition_in(infoconfirm.$$.fragment, local);
    			current = true;
    		},
    		o: function outro(local) {
    			transition_out(infoconfirm.$$.fragment, local);
    			current = false;
    		},
    		d: function destroy(detaching) {
    			destroy_component(infoconfirm, detaching);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_if_block_2.name,
    		type: "if",
    		source: "(34:41) ",
    		ctx
    	});

    	return block;
    }

    // (32:39) 
    function create_if_block_1(ctx) {
    	let infoinput;
    	let current;
    	infoinput = new InfoInput({ $$inline: true });
    	infoinput.$on("finish", /*finishInfoInput*/ ctx[3]);
    	infoinput.$on("goToWelcome", /*goToWelcome*/ ctx[5]);

    	const block = {
    		c: function create() {
    			create_component(infoinput.$$.fragment);
    		},
    		m: function mount(target, anchor) {
    			mount_component(infoinput, target, anchor);
    			current = true;
    		},
    		p: noop,
    		i: function intro(local) {
    			if (current) return;
    			transition_in(infoinput.$$.fragment, local);
    			current = true;
    		},
    		o: function outro(local) {
    			transition_out(infoinput.$$.fragment, local);
    			current = false;
    		},
    		d: function destroy(detaching) {
    			destroy_component(infoinput, detaching);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_if_block_1.name,
    		type: "if",
    		source: "(32:39) ",
    		ctx
    	});

    	return block;
    }

    // (30:1) {#if currentPage === 'welcome'}
    function create_if_block(ctx) {
    	let welcome;
    	let current;
    	welcome = new Welcome({ $$inline: true });
    	welcome.$on("start", /*startInfoInput*/ ctx[2]);

    	const block = {
    		c: function create() {
    			create_component(welcome.$$.fragment);
    		},
    		m: function mount(target, anchor) {
    			mount_component(welcome, target, anchor);
    			current = true;
    		},
    		p: noop,
    		i: function intro(local) {
    			if (current) return;
    			transition_in(welcome.$$.fragment, local);
    			current = true;
    		},
    		o: function outro(local) {
    			transition_out(welcome.$$.fragment, local);
    			current = false;
    		},
    		d: function destroy(detaching) {
    			destroy_component(welcome, detaching);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_if_block.name,
    		type: "if",
    		source: "(30:1) {#if currentPage === 'welcome'}",
    		ctx
    	});

    	return block;
    }

    function create_fragment(ctx) {
    	let main;
    	let current_block_type_index;
    	let if_block;
    	let current;
    	const if_block_creators = [create_if_block, create_if_block_1, create_if_block_2];
    	const if_blocks = [];

    	function select_block_type(ctx, dirty) {
    		if (/*currentPage*/ ctx[0] === 'welcome') return 0;
    		if (/*currentPage*/ ctx[0] === 'infoInput') return 1;
    		if (/*currentPage*/ ctx[0] === 'infoConfirm') return 2;
    		return -1;
    	}

    	if (~(current_block_type_index = select_block_type(ctx))) {
    		if_block = if_blocks[current_block_type_index] = if_block_creators[current_block_type_index](ctx);
    	}

    	const block = {
    		c: function create() {
    			main = element("main");
    			if (if_block) if_block.c();
    			attr_dev(main, "class", "svelte-11yobjg");
    			add_location(main, file, 28, 0, 556);
    		},
    		l: function claim(nodes) {
    			throw new Error("options.hydrate only works if the component was compiled with the `hydratable: true` option");
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, main, anchor);

    			if (~current_block_type_index) {
    				if_blocks[current_block_type_index].m(main, null);
    			}

    			current = true;
    		},
    		p: function update(ctx, [dirty]) {
    			let previous_block_index = current_block_type_index;
    			current_block_type_index = select_block_type(ctx);

    			if (current_block_type_index === previous_block_index) {
    				if (~current_block_type_index) {
    					if_blocks[current_block_type_index].p(ctx, dirty);
    				}
    			} else {
    				if (if_block) {
    					group_outros();

    					transition_out(if_blocks[previous_block_index], 1, 1, () => {
    						if_blocks[previous_block_index] = null;
    					});

    					check_outros();
    				}

    				if (~current_block_type_index) {
    					if_block = if_blocks[current_block_type_index];

    					if (!if_block) {
    						if_block = if_blocks[current_block_type_index] = if_block_creators[current_block_type_index](ctx);
    						if_block.c();
    					} else {
    						if_block.p(ctx, dirty);
    					}

    					transition_in(if_block, 1);
    					if_block.m(main, null);
    				} else {
    					if_block = null;
    				}
    			}
    		},
    		i: function intro(local) {
    			if (current) return;
    			transition_in(if_block);
    			current = true;
    		},
    		o: function outro(local) {
    			transition_out(if_block);
    			current = false;
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(main);

    			if (~current_block_type_index) {
    				if_blocks[current_block_type_index].d();
    			}
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_fragment.name,
    		type: "component",
    		source: "",
    		ctx
    	});

    	return block;
    }

    function instance($$self, $$props, $$invalidate) {
    	let { $$slots: slots = {}, $$scope } = $$props;
    	validate_slots('App', slots, []);
    	let currentPage = 'welcome';
    	let userInfo = {};

    	function startInfoInput() {
    		$$invalidate(0, currentPage = 'infoInput');
    	}

    	function finishInfoInput(event) {
    		$$invalidate(1, userInfo = event.detail);
    		$$invalidate(0, currentPage = 'infoConfirm');
    	}

    	function goBack() {
    		if (currentPage === 'infoConfirm') {
    			$$invalidate(0, currentPage = 'infoInput');
    		}
    	}

    	function goToWelcome() {
    		$$invalidate(0, currentPage = 'welcome');
    	}

    	const writable_props = [];

    	Object.keys($$props).forEach(key => {
    		if (!~writable_props.indexOf(key) && key.slice(0, 2) !== '$$' && key !== 'slot') console.warn(`<App> was created with unknown prop '${key}'`);
    	});

    	$$self.$capture_state = () => ({
    		Welcome,
    		InfoInput,
    		InfoConfirm,
    		currentPage,
    		userInfo,
    		startInfoInput,
    		finishInfoInput,
    		goBack,
    		goToWelcome
    	});

    	$$self.$inject_state = $$props => {
    		if ('currentPage' in $$props) $$invalidate(0, currentPage = $$props.currentPage);
    		if ('userInfo' in $$props) $$invalidate(1, userInfo = $$props.userInfo);
    	};

    	if ($$props && "$$inject" in $$props) {
    		$$self.$inject_state($$props.$$inject);
    	}

    	return [currentPage, userInfo, startInfoInput, finishInfoInput, goBack, goToWelcome];
    }

    class App extends SvelteComponentDev {
    	constructor(options) {
    		super(options);
    		init(this, options, instance, create_fragment, safe_not_equal, {});

    		dispatch_dev("SvelteRegisterComponent", {
    			component: this,
    			tagName: "App",
    			options,
    			id: create_fragment.name
    		});
    	}
    }

    const app = new App({
    	target: document.body,
    	props: {
    		name: '사용자'
    	}
    });

    return app;

})();
//# sourceMappingURL=bundle.js.map
