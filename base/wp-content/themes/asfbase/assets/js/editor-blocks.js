/**
 * Editor previews for the theme's PHP-rendered blocks. (The asfbase-core plugin ships its own copy for hm/* blocks, so neither depends on the other.)
 *
 * Plain JS on the wp.* globals, so there is no build step. Title, attributes and
 * settings come from each block.json (bootstrapped by the server); here we only
 * supply an edit() that previews the PHP render. To add a block: point its
 * block.json "editorScript" at "asfbase-editor-blocks" and list its name below.
 */
( function ( wp ) {
	const el = wp.element.createElement;
	const { useBlockProps } = wp.blockEditor;
	const ServerSideRender = wp.serverSideRender;

	[ 'asfbase/site-header', 'asfbase/site-footer', 'asfbase/hero-visual' ].forEach( function ( name ) {
		if ( wp.blocks.getBlockType( name ) ) {
			return;
		}
		wp.blocks.registerBlockType( name, {
			edit: function ( props ) {
				return el(
					'div',
					useBlockProps( { style: { pointerEvents: 'none' } } ),
					el( ServerSideRender, { block: name, attributes: props.attributes } )
				);
			},
			save: function () {
				return null;
			},
		} );
	} );
} )( window.wp );
