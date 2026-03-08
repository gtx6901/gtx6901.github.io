/**
 * 自定义样式注入：
 * - 固定 reward 二维码图片为统一尺寸，避免不同分辨率图片显示大小不一致
 */
hexo.extend.injector.register('head_end', () => {
  return `<style>
#qr img {
  width: 180px;
  height: 180px;
  object-fit: contain;
}
</style>`;
});

/**
 * 生成前清理主题 reward.account 里值为 null/空 的 key，
 * 防止主题默认配置里的 paypal 等条目被渲染出来
 */
hexo.extend.filter.register('before_generate', function () {
  const account = hexo.theme.config.reward && hexo.theme.config.reward.account;
  if (account) {
    Object.keys(account).forEach(key => {
      if (!account[key]) {
        delete account[key];
      }
    });
  }
});
