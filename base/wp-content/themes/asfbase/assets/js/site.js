/**
 * ASF Base front-end behaviour. Vanilla JS, no dependencies, loaded deferred.
 *
 * Each feature is a small init function that no-ops when its markup isn't on
 * the page. Motion respects prefers-reduced-motion throughout.
 *
 *   header()      sticky header: solid after scroll, hides on scroll down
 *   megaMenu()    Services panel: hover intent, click, Esc, focus-out
 *   mobileMenu()  full-screen menu with scroll lock
 *   reveal()      auto-tags sections' children and reveals them on scroll
 *   heroLines()   splits the hero H1 at <br> so lines rise in
 *   countUp()     animates .hm-stat__num values when they enter view
 *   marquee()     duplicates the client list for a seamless loop
 *   magnetic()    subtle pull on primary CTAs (fine pointers only)
 *   parallax()    hero collage layers drift with the pointer ([data-depth])
 *   track()       dataLayer events for CTAs, calls, bookings (GA4/GTM)
 *   briefForm()   multi-step lead form → /wp-json/asfbase/v1/leads
 *   newsletter()  footer signup → same endpoint, type "newsletter"
 *   calendly()    lazy inline Calendly embed on the contact page
 */
( function () {
	'use strict';

	const root = document.documentElement;
	const reduceMotion = window.matchMedia( '(prefers-reduced-motion: reduce)' ).matches;
	const finePointer = window.matchMedia( '(pointer: fine)' ).matches;
	const cfg = window.ASFBASE || {};
	window.__hmReady = true;
	root.classList.add( 'hm-js' );

	const $ = ( sel, ctx = document ) => ctx.querySelector( sel );
	const $$ = ( sel, ctx = document ) => Array.from( ctx.querySelectorAll( sel ) );

	window.dataLayer = window.dataLayer || [];
	const push = ( event, data = {} ) => {
		window.dataLayer.push( Object.assign( { event }, data ) );
		// GA4 without GTM: the plugin's analytics module sets asfGtagEvents so these reach GA4 as events too.
		if ( window.asfGtagEvents && typeof window.gtag === 'function' ) window.gtag( 'event', event, data );
	};

	/* Header ------------------------------------------------------------- */
	function header() {
		const el = $( '[data-header]' );
		if ( ! el ) return;
		let lastY = window.scrollY;
		let ticking = false;
		const update = () => {
			const y = window.scrollY;
			el.classList.toggle( 'is-scrolled', y > 24 );
			const goingDown = y > lastY && y > 320;
			if ( ! el.classList.contains( 'is-open' ) ) el.classList.toggle( 'is-hidden', goingDown );
			lastY = y;
			ticking = false;
		};
		window.addEventListener( 'scroll', () => {
			if ( ! ticking ) {
				window.requestAnimationFrame( update );
				ticking = true;
			}
		}, { passive: true } );
		update();
	}

	/* Mega menu ------------------------------------------------------------ */
	function megaMenu() {
		const header = $( '[data-header]' );
		const btn = $( '.hm-nav__item.has-mega > button' );
		const panel = btn && document.getElementById( btn.getAttribute( 'aria-controls' ) );
		if ( ! btn || ! panel ) return;
		let closeTimer;

		const open = () => {
			clearTimeout( closeTimer );
			if ( btn.getAttribute( 'aria-expanded' ) === 'true' ) return;
			panel.hidden = false;
			btn.setAttribute( 'aria-expanded', 'true' );
			header.classList.add( 'is-open' );
			requestAnimationFrame( () => panel.classList.add( 'is-open' ) );
		};
		const close = ( immediate ) => {
			clearTimeout( closeTimer );
			const run = () => {
				btn.setAttribute( 'aria-expanded', 'false' );
				panel.classList.remove( 'is-open' );
				header.classList.remove( 'is-open' );
				setTimeout( () => { if ( btn.getAttribute( 'aria-expanded' ) === 'false' ) panel.hidden = true; }, 300 );
			};
			immediate ? run() : ( closeTimer = setTimeout( run, 180 ) );
		};

		btn.addEventListener( 'click', () => ( btn.getAttribute( 'aria-expanded' ) === 'true' ? close( true ) : open() ) );
		if ( finePointer ) {
			[ btn, panel ].forEach( ( n ) => {
				n.addEventListener( 'mouseenter', open );
				n.addEventListener( 'mouseleave', () => close() );
			} );
		}
		document.addEventListener( 'keydown', ( e ) => {
			if ( e.key === 'Escape' && btn.getAttribute( 'aria-expanded' ) === 'true' ) {
				close( true );
				btn.focus();
			}
		} );
		panel.addEventListener( 'focusout', ( e ) => {
			if ( ! panel.contains( e.relatedTarget ) && e.relatedTarget !== btn ) close( true );
		} );
	}

	/* Mobile menu --------------------------------------------------------- */
	function mobileMenu() {
		const header = $( '[data-header]' );
		const btn = $( '.hm-burger' );
		const panel = $( '#hm-mobile' );
		if ( ! btn || ! panel ) return;
		const set = ( openState ) => {
			btn.setAttribute( 'aria-expanded', String( openState ) );
			$( '.hm-burger__label', btn ).textContent = openState ? 'Close' : 'Menu';
			panel.hidden = ! openState;
			header.classList.toggle( 'is-open', openState );
			document.body.style.overflow = openState ? 'hidden' : '';
		};
		btn.addEventListener( 'click', () => set( btn.getAttribute( 'aria-expanded' ) !== 'true' ) );
		document.addEventListener( 'keydown', ( e ) => {
			if ( e.key === 'Escape' && btn.getAttribute( 'aria-expanded' ) === 'true' ) {
				set( false );
				btn.focus();
			}
		} );
		window.matchMedia( '(min-width: 1081px)' ).addEventListener( 'change', ( mq ) => mq.matches && set( false ) );
	}

	/* Reveal on scroll ---------------------------------------------------- */
	const REVEAL = [
		'.hm-section:not(.hm-hero):not(.hm-marquee) > *:not(.hm-index):not(.hm-work):not(.hm-stats):not(.hm-steps):not(.hm-offers):not(.hm-features):not(.hm-pains):not(.hm-grid):not(.hm-bento):not(.hm-gallery):not(.hm-faces)',
		'.hm-index__row', '.hm-work__item', '.hm-stat', '.hm-step', '.hm-offer', '.hm-feature', '.hm-pain', '.hm-grid > *', '.hm-tile', '.hm-gallery > *', '.hm-face',
		'.hm-hero__foot > *', '.hm-chain', '.hm-footer [data-reveal]',
	].join( ',' );

	function reveal() {
		if ( reduceMotion || ! ( 'IntersectionObserver' in window ) ) {
			$$( '.hm-step' ).forEach( ( s ) => s.classList.add( 'is-in' ) );
			return;
		}
		// Only below-the-fold elements animate; what's already on screen stays put (no flicker, no LCP delay).
		const fold = window.innerHeight * 0.92;
		const items = $$( REVEAL ).filter( ( el ) => el.getBoundingClientRect().top > fold );
		$$( '.hm-step' ).forEach( ( s ) => s.getBoundingClientRect().top <= fold && s.classList.add( 'is-in' ) );
		items.forEach( ( el ) => {
			el.setAttribute( 'data-reveal', '' );
			const siblings = Array.from( el.parentElement.children ).filter( ( c ) => c.matches( REVEAL ) );
			el.style.setProperty( '--i', String( Math.min( siblings.indexOf( el ), 6 ) ) );
		} );
		const io = new IntersectionObserver( ( entries ) => {
			entries.forEach( ( entry ) => {
				if ( entry.isIntersecting ) {
					entry.target.classList.add( 'is-in' );
					io.unobserve( entry.target );
				}
			} );
		}, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 } );
		items.forEach( ( el ) => io.observe( el ) );
	}

	/* Hero headline lines ------------------------------------------------- */
	function heroLines() {
		const h1 = $( '.hm-hero h1' );
		if ( ! h1 ) return;
		if ( ! reduceMotion ) {
			const parts = h1.innerHTML.split( /<br\s*\/?>/i );
			h1.innerHTML = parts.map( ( p, i ) => `<span class="hm-line" style="--i:${ i }"><span>${ p.trim() }</span></span>` ).join( ' ' );
		}
		h1.classList.add( 'is-split' );
		requestAnimationFrame( () => requestAnimationFrame( () => h1.classList.add( 'is-in' ) ) );
	}

	/* Count-up numbers ----------------------------------------------------- */
	const useCommaIn = ( n ) => n.includes( ',' );
	function countUp() {
		const nums = $$( '.hm-stat__num' );
		if ( ! nums.length || reduceMotion || ! ( 'IntersectionObserver' in window ) ) return;
		const animate = ( el ) => {
			const node = Array.from( el.childNodes ).find( ( n ) => n.nodeType === 3 && /\d/.test( n.textContent ) );
			if ( ! node ) return;
			const raw = node.textContent;
			const match = raw.match( /[\d,.]+/ );
			if ( ! match ) return;
			const target = parseFloat( match[ 0 ].replace( /,/g, '' ) );
			// Leave years and labelled values ("Since 2015", class is-static) as written.
			if ( el.classList.contains( 'is-static' ) || ( target >= 1900 && target <= 2100 && ! useCommaIn( match[ 0 ] ) ) || /[a-z]/i.test( raw.slice( 0, raw.indexOf( match[ 0 ] ) ) ) ) return;
			const decimals = ( match[ 0 ].split( '.' )[ 1 ] || '' ).length;
			const useComma = match[ 0 ].includes( ',' );
			const fmt = ( v ) => {
				const s = v.toFixed( decimals );
				return useComma ? Number( s ).toLocaleString( 'en-US', { minimumFractionDigits: decimals } ) : s;
			};
			const start = performance.now();
			const dur = 1600;
			const tick = ( t ) => {
				const p = Math.min( ( t - start ) / dur, 1 );
				const eased = 1 - Math.pow( 1 - p, 4 );
				node.textContent = raw.replace( match[ 0 ], fmt( target * eased ) );
				if ( p < 1 ) requestAnimationFrame( tick );
				else node.textContent = raw;
			};
			requestAnimationFrame( tick );
		};
		const io = new IntersectionObserver( ( entries ) => {
			entries.forEach( ( e ) => {
				if ( e.isIntersecting ) {
					animate( e.target );
					io.unobserve( e.target );
				}
			} );
		}, { threshold: 0.4 } );
		nums.forEach( ( n ) => io.observe( n ) );
	}

	/* Marquee -------------------------------------------------------------- */
	function marquee() {
		$$( '.hm-marquee ul' ).forEach( ( list ) => {
			if ( list.dataset.cloned ) return;
			Array.from( list.children ).forEach( ( li ) => {
				const clone = li.cloneNode( true );
				clone.setAttribute( 'aria-hidden', 'true' );
				list.appendChild( clone );
			} );
			list.dataset.cloned = '1';
		} );
	}

	/* Magnetic CTAs -------------------------------------------------------- */
	function magnetic() {
		if ( ! finePointer || reduceMotion ) return;
		$$( '.hm-hero .wp-block-button__link, .hm-footer__cta .hm-btn' ).forEach( ( btn ) => {
			btn.addEventListener( 'mousemove', ( e ) => {
				const r = btn.getBoundingClientRect();
				const x = ( e.clientX - r.left - r.width / 2 ) * 0.18;
				const y = ( e.clientY - r.top - r.height / 2 ) * 0.3;
				btn.style.transform = `translate(${ x }px, ${ y }px)`;
			} );
			btn.addEventListener( 'mouseleave', () => ( btn.style.transform = '' ) );
		} );
	}

	/* Hero collage parallax ------------------------------------------------- */
	function parallax() {
		const scene = $( '[data-parallax]' );
		if ( ! scene || ! finePointer || reduceMotion ) return;
		const layers = $$( '[data-depth]', scene );
		let raf = 0;
		window.addEventListener( 'pointermove', ( e ) => {
			cancelAnimationFrame( raf );
			raf = requestAnimationFrame( () => {
				const x = e.clientX / window.innerWidth - 0.5;
				const y = e.clientY / window.innerHeight - 0.5;
				layers.forEach( ( l ) => {
					const d = parseFloat( l.dataset.depth ) * 100;
					l.style.transform = `translate3d(${ ( -x * d ).toFixed( 2 ) }px, ${ ( -y * d ).toFixed( 2 ) }px, 0)`;
				} );
			} );
		}, { passive: true } );
	}

	/* Analytics ------------------------------------------------------------ */
	function track() {
		document.addEventListener( 'click', ( e ) => {
			const a = e.target.closest( 'a, button' );
			if ( ! a ) return;
			const href = a.getAttribute( 'href' ) || '';
			const label = ( a.textContent || '' ).trim().slice( 0, 80 );
			const section = a.closest( 'section, header, footer, [class*="hm-"]' );
			const location = a.dataset.cta || ( section && ( section.className.match( /hm-[a-z-]+/ ) || [ '' ] )[ 0 ] ) || '';
			if ( href.startsWith( 'tel:' ) ) push( 'phone_click', { location } );
			if ( /calendly\.com/.test( href ) || a.hasAttribute( 'data-booking' ) ) push( 'book_call_open', { location, label } );
			if ( a.dataset.cta || a.classList.contains( 'wp-block-button__link' ) || a.classList.contains( 'hm-btn' ) ) push( 'cta_click', { label, location, href } );
		} );
		if ( 'IntersectionObserver' in window ) {
			const io = new IntersectionObserver( ( entries ) => {
				entries.forEach( ( e ) => {
					if ( e.isIntersecting ) {
						const title = $( 'h3', e.target );
						push( 'offer_view', { offer: title ? title.textContent.trim() : '' } );
						io.unobserve( e.target );
					}
				} );
			}, { threshold: 0.6 } );
			$$( '.hm-offer' ).forEach( ( o ) => io.observe( o ) );
		}
	}

	/* Attribution: where this visit came from ---------------------------------
	 * The visit's first page (or a later one that arrives with campaign tags) is
	 * remembered for the session: its path, the outside referrer and the tags.
	 * Every lead carries it, so an enquiry sent from /contact/ still credits the
	 * ad or email that brought the visitor in. Where consent is required, nothing
	 * is stored until window.asfConsent.grant(); a form on the landing page itself
	 * is attributed either way. */
	const TAGS = [ 'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'gclid', 'gbraid', 'wbraid', 'fbclid', 'msclkid', 'li_fat_id' ];
	const visit = ( () => {
		const q = new URLSearchParams( window.location.search );
		const utm = {};
		TAGS.forEach( ( k ) => q.get( k ) && ( utm[ k ] = q.get( k ).slice( 0, 100 ) ) );
		let referrer = '';
		try {
			referrer = document.referrer && new URL( document.referrer ).host !== window.location.host ? document.referrer : '';
		} catch ( err ) {}
		return { landing: window.location.pathname, referrer, utm };
	} )();
	const remember = () => {
		if ( window.asfConsentRequired && ! window.asfConsentGranted ) return;
		try {
			// A new campaign click replaces the remembered touch; otherwise the first page wins.
			if ( ! sessionStorage.getItem( 'hm_touch' ) || Object.keys( visit.utm ).length ) {
				sessionStorage.setItem( 'hm_touch', JSON.stringify( visit ) );
			}
		} catch ( err ) {}
	};
	const touch = () => {
		try {
			return JSON.parse( sessionStorage.getItem( 'hm_touch' ) || 'null' ) || visit;
		} catch ( err ) {
			return visit;
		}
	};
	remember();
	document.addEventListener( 'asf:consent', remember );

	/* Lead capture ------------------------------------------------------------ */
	const send = ( payload ) => {
		const t = touch();
		return fetch( cfg.leadEndpoint, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify( Object.assign( {
				page: window.location.pathname,
				landing: t.landing,
				referrer: t.referrer,
				utm: t.utm,
				elapsed: Math.round( performance.now() / 1000 ),
			}, payload ) ),
		} ).then( ( r ) => r.json().then( ( body ) => ( { ok: r.ok, body } ) ) );
	};

	/* Multi-step brief form ------------------------------------------------ */
	function briefForm() {
		$$( 'form[data-brief]' ).forEach( ( form ) => {
			const steps = $$( '.hm-form__step', form );
			const back = $( '.hm-form__back', form );
			const next = $( '[data-next]', form );
			const submit = $( '[type="submit"]', form );
			const msg = $( '.hm-form__msg', form );
			const bars = $$( '.hm-form__progress i', form );
			const counter = $( '.hm-form__count', form );
			let current = 0;
			form.setAttribute( 'data-steps', '' );

			const show = ( i ) => {
				current = i;
				steps.forEach( ( s, n ) => s.classList.toggle( 'is-active', n === i ) );
				bars.forEach( ( b, n ) => b.classList.toggle( 'is-done', n <= i ) );
				if ( counter ) counter.textContent = `${ i + 1 } / ${ steps.length }`;
				back.hidden = i === 0;
				next.hidden = i === steps.length - 1;
				submit.hidden = i !== steps.length - 1;
				msg.textContent = '';
				msg.classList.remove( 'is-error' );
			};

			const valid = ( step ) => {
				let ok = true;
				$$( '[required]', step ).forEach( ( f ) => {
					const group = f.type === 'radio' || f.type === 'checkbox' ? $$( `[name="${ f.name }"]`, step ) : null;
					const filled = group ? group.some( ( g ) => g.checked ) : f.value.trim() && f.checkValidity();
					f.setAttribute( 'aria-invalid', filled ? 'false' : 'true' );
					if ( ! filled ) ok = false;
				} );
				if ( ! ok ) {
					msg.textContent = 'A couple of answers are missing. Mind filling them in?';
					msg.classList.add( 'is-error' );
				}
				return ok;
			};

			next.addEventListener( 'click', () => valid( steps[ current ] ) && show( current + 1 ) );
			back.addEventListener( 'click', () => show( current - 1 ) );
			// A step made only of single-choice questions moves on once every one is answered.
			steps.forEach( ( step, i ) => {
				const radios = $$( 'input[type="radio"]', step );
				if ( ! radios.length || $$( 'input:not([type="radio"]), textarea', step ).length ) return;
				const groups = [ ...new Set( radios.map( ( r ) => r.name ) ) ];
				step.addEventListener( 'change', () => {
					const done = groups.every( ( g ) => $( `input[name="${ g }"]:checked`, step ) );
					if ( done && i < steps.length - 1 ) setTimeout( () => show( i + 1 ), 260 );
				} );
			} );

			form.addEventListener( 'submit', ( e ) => {
				e.preventDefault();
				if ( ! valid( steps[ current ] ) ) return;
				const data = new FormData( form );
				const payload = { type: 'brief', needs: data.getAll( 'needs[]' ) };
				data.forEach( ( v, k ) => { if ( k !== 'needs[]' ) payload[ k ] = v; } );
				submit.disabled = true;
				msg.textContent = 'Sending…';
				send( payload ).then( ( { ok, body } ) => {
					if ( ! ok ) throw new Error( ( body && body.message ) || 'error' );
					push( 'lead_submit', { budget: payload.budget || '', needs: payload.needs.join( '|' ) } );
					window.location.href = cfg.thankYou || '/thank-you/';
				} ).catch( ( err ) => {
					submit.disabled = false;
					msg.textContent = err.message && err.message !== 'error' ? err.message : 'Something went wrong. Please call us or try again.';
					msg.classList.add( 'is-error' );
				} );
			} );
			show( 0 );
		} );
	}

	/* Newsletter ------------------------------------------------------------ */
	function newsletter() {
		$$( 'form[data-newsletter]' ).forEach( ( form ) => {
			const msg = $( '.hm-newsletter__msg', form );
			form.addEventListener( 'submit', ( e ) => {
				e.preventDefault();
				const email = form.email.value.trim();
				if ( ! email || ! form.email.checkValidity() ) {
					msg.textContent = 'That email doesn’t look right.';
					return;
				}
				msg.textContent = 'Adding you…';
				send( { type: 'newsletter', email, company_url: form.company_url.value } ).then( ( { ok } ) => {
					msg.textContent = ok ? 'You’re in. First brief lands next month.' : 'Couldn’t sign you up. Try again?';
					if ( ok ) {
						form.reset();
						push( 'newsletter_signup' );
					}
				} );
			} );
		} );
	}

	/* Calendly inline embed (contact page) ----------------------------------- */
	function calendly() {
		$$( '[data-calendly-embed]' ).forEach( ( wrap ) => {
			const btn = $( 'button', wrap );
			if ( ! btn ) return;
			btn.addEventListener( 'click', () => {
				const url = new URL( wrap.dataset.calendlyEmbed );
				url.searchParams.set( 'embed_domain', window.location.host );
				url.searchParams.set( 'embed_type', 'Inline' );
				url.searchParams.set( 'primary_color', 'f7941d' );
				url.searchParams.set( 'hide_gdpr_banner', '1' );
				const frame = document.createElement( 'iframe' );
				frame.src = url.toString();
				frame.title = 'Book a 30-minute call';
				frame.loading = 'lazy';
				frame.style.cssText = 'width:100%;height:700px;border:0;border-radius:8px;background:#fff';
				wrap.replaceChildren( frame );
				push( 'book_call_open', { location: 'contact-embed' } );
			} );
		} );
	}

	const init = () => {
		header();
		megaMenu();
		mobileMenu();
		heroLines();
		reveal();
		countUp();
		marquee();
		magnetic();
		parallax();
		track();
		briefForm();
		newsletter();
		calendly();
	};
	document.readyState === 'loading' ? document.addEventListener( 'DOMContentLoaded', init ) : init();
} )();
