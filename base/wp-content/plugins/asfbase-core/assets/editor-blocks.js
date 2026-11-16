/**
 * Editor previews for the plugin's PHP-rendered blocks. (The theme ships its own copy for asfbase/* blocks, so neither depends on the other.)
 *
 * Plain JS on the wp.* globals, so there is no build step. Title, attributes and
 * settings come from each block.json (bootstrapped by the server); here we only
 * supply an edit() that previews the PHP render. To add a block: point its
 * block.json "editorScript" at "hm-editor-blocks" and list its name below.
 */
( function ( wp ) {
	const el = wp.element.createElement;
	const { useBlockProps } = wp.blockEditor;
	const ServerSideRender = wp.serverSideRender;

	[ 'hm/work-grid', 'hm/brief-form', 'hm/case-header', 'hm/case-next' ].forEach( function ( name ) {
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
