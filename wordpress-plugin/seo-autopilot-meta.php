<?php
/**
 * Plugin Name: SEO Autopilot – helper
 * Description: Lets SEO Autopilot set Rank Math / Yoast SEO fields and the Divi Builder flag through the REST API.
 * Version: 2.0
 *
 * Install: upload this file to wp-content/mu-plugins/ (create the folder if missing)
 * or zip it and install it as a normal plugin. Works with Rank Math or Yoast, Divi or Elementor.
 * It only exposes these fields to logged-in users who can edit posts — nothing public.
 */
if ( ! defined( 'ABSPATH' ) ) { exit; }

add_action( 'init', function () {
	$keys = array(
		// Rank Math
		'rank_math_title', 'rank_math_description', 'rank_math_focus_keyword',
		// Yoast (if a site uses it instead)
		'_yoast_wpseo_title', '_yoast_wpseo_metadesc', '_yoast_wpseo_focuskw',
		// Divi Builder
		'_et_pb_use_builder', '_et_pb_page_layout', '_et_pb_old_content',
	);
	foreach ( $keys as $key ) {
		register_post_meta( 'post', $key, array(
			'type'          => 'string',
			'single'        => true,
			'show_in_rest'  => true,
			'auth_callback' => function () { return current_user_can( 'edit_posts' ); },
		) );
	}
} );
