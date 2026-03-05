/* global hexo */

'use strict';

const { url_for } = require('hexo-util');

hexo.extend.helper.register('_image_url', function(img, path = '') {
  const { statics } = hexo.theme.config;
  const { post_asset_folder } = hexo.config;

  if (!img) return '';

  if (img.startsWith('//') || img.startsWith('http')) {
    return img;
  }

  const normalizedStatics = statics.endsWith('/') ? statics : `${statics}/`;
  const normalizedPath = post_asset_folder
    ? String(path || '').replace(/^\/+/, '').replace(/index\.html$/, '')
    : '';
  const normalizedImg = String(img || '').replace(/^\/+/, '');

  return url_for.call(this, `${normalizedStatics}${normalizedPath}${normalizedImg}`);
});
