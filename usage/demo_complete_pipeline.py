"""
jmcomic 完整流程演示脚本
=======================
功能：下载本子 → 转长图 → 重命名 → 打包

使用方法：
    python demo_complete_pipeline.py

注意：
    - 需要先配置好网络环境（如果需要代理）
    - 可以通过环境变量或修改下方配置来定制
"""
import os
import sys

from jmcomic import (
    JmOption, JmModuleConfig, DirRule,
    download_album, Feature,
    create_option, fix_suffix, mkdir_if_not_exists,
)


# ============================================================
#  配置区域 —— 你可以修改这里的参数
# ============================================================

CONFIG = {
    # 本子ID（可以填多个）
    'album_ids': ['350234'],

    # 下载根目录
    'download_dir': './download/',

    # 长图输出目录
    'long_img_dir': './output/long_img/',

    # 客户端类型: 'api' (移动端) 或 'html' (网页端)
    'client_impl': 'api',

    # 图片格式转换: ''(保持原格式), 'png', 'jpg', 'webp'
    'image_suffix': 'png',

    # 长图相关
    'long_img': {
        'enable': True,           # 是否生成长图
        'level': 'album',         # 合并维度: 'album'(整本) 或 'photo'(每章)
        # 命名规则 —— 支持的变量:
        #   {Aid}     本子ID
        #   {Atitle}  本子标题
        #   {Aauthor} 作者
        #   {Pid}     章节ID
        #   {Ptitle}  章节标题
        #   {Pindex}  章节序号
        'filename_rule': '[JM{Aid}]_{Atitle}',
        'delete_original': False,  # 生成长图后是否删除原图
    },

    # 登录（可选，不填则匿名下载）
    'login': {
        'username': '',
        'password': '',
    },

    # 下载路径规则
    'dir_rule': 'Bd_Aauthor_Atitle_Pindex',
}


# ============================================================
#  构建 Option 配置对象
# ============================================================

def build_option(config: dict) -> JmOption:
    """根据配置字典构建 JmOption 对象"""

    download_dir = os.path.abspath(config['download_dir'])
    mkdir_if_not_exists(download_dir)

    # 创建默认 option
    option = JmModuleConfig.option_class().default()

    # 配置客户端实现
    option.client.impl = config['client_impl']

    # 配置下载目录规则
    option.dir_rule = DirRule(
        rule=config['dir_rule'],
        base_dir=download_dir,
    )

    # 配置图片格式转换
    suffix = config.get('image_suffix', '')
    if suffix:
        option.download.image.suffix = fix_suffix(suffix)

    # 配置登录插件
    login_cfg = config.get('login', {})
    if login_cfg.get('username') and login_cfg.get('password'):
        option.plugins.setdefault('after_init', [])
        option.plugins['after_init'].append({
            'plugin': 'login',
            'kwargs': {
                'username': login_cfg['username'],
                'password': login_cfg['password'],
            }
        })

    # 配置长图插件
    long_img_cfg = config.get('long_img', {})
    if long_img_cfg.get('enable'):
        call_when = 'after_album' if long_img_cfg.get('level') == 'album' else 'after_photo'
        long_img_dir = os.path.abspath(config['long_img_dir'])
        mkdir_if_not_exists(long_img_dir)

        option.plugins.setdefault(call_when, [])
        option.plugins[call_when].append({
            'plugin': 'long_img',
            'kwargs': {
                'img_dir': long_img_dir,
                'filename_rule': long_img_cfg.get('filename_rule', '[JM{Aid}]_{Atitle}'),
                'delete_original_file': long_img_cfg.get('delete_original', False),
            }
        })

    return option


# ============================================================
#  方式一：使用 Feature 机制（推荐，更简洁）
# ============================================================

def run_with_feature(config: dict):
    """使用 Feature 机制，代码最简洁"""
    print('=' * 60)
    print('  方式一：使用 Feature 机制')
    print('=' * 60)

    download_dir = os.path.abspath(config['download_dir'])
    mkdir_if_not_exists(download_dir)

    option = JmModuleConfig.option_class().default()
    option.client.impl = config['client_impl']
    option.dir_rule = DirRule(config['dir_rule'], base_dir=download_dir)

    suffix = config.get('image_suffix', '')
    if suffix:
        option.download.image.suffix = fix_suffix(suffix)

    # 使用 Feature —— 一行代码搞定长图
    extra = Feature.export_long_img(
        img_dir=os.path.abspath(config['long_img_dir']),
        filename_rule=config['long_img'].get('filename_rule', '[JM{Aid}]_{Atitle}'),
        delete_original_file=config['long_img'].get('delete_original', False),
    )

    for aid in config['album_ids']:
        print(f'\n🚀 下载本子: {aid}')
        album, downloader = download_album(aid, option, extra=extra)
        print(f'✅ 完成: {album.name}')

    print('\n🎉 Feature 方式完成！')


# ============================================================
#  方式二：使用插件机制（灵活，适合复杂场景）
# ============================================================

def run_with_plugin(config: dict):
    """使用插件机制，更灵活可控"""
    print('\n' + '=' * 60)
    print('  方式二：使用插件机制')
    print('=' * 60)

    option = build_option(config)

    for aid in config['album_ids']:
        print(f'\n🚀 下载本子: {aid}')
        album, downloader = download_album(aid, option)
        print(f'✅ 完成: {album.name}')

    print('\n🎉 插件方式完成！')


# ============================================================
#  方式三：手动调用长图插件（完全控制）
# ============================================================

def run_manual(config: dict):
    """手动控制每一步，最灵活"""
    print('\n' + '=' * 60)
    print('  方式三：手动控制每一步')
    print('=' * 60)

    download_dir = os.path.abspath(config['download_dir'])
    long_img_dir = os.path.abspath(config['long_img_dir'])
    mkdir_if_not_exists(download_dir)
    mkdir_if_not_exists(long_img_dir)

    option = JmModuleConfig.option_class().default()
    option.client.impl = config['client_impl']
    option.dir_rule = DirRule(config['dir_rule'], base_dir=download_dir)

    suffix = config.get('image_suffix', '')
    if suffix:
        option.download.image.suffix = fix_suffix(suffix)

    for aid in config['album_ids']:
        print(f'\n📥 步骤1: 下载本子 {aid}')
        album, downloader = download_album(aid, option)
        print(f'   → 下载完成: {album.name}')

        print(f'🖼️  步骤2: 生成长图')
        from jmcomic import LongImgPlugin
        plugin = LongImgPlugin.build(option)
        plugin.invoke(
            album=album,
            downloader=downloader,
            img_dir=long_img_dir,
            filename_rule=config['long_img'].get('filename_rule', '[JM{Aid}]_{Atitle}'),
            delete_original_file=config['long_img'].get('delete_original', False),
        )
        print(f'   → 长图已生成到: {long_img_dir}')

    print('\n🎉 手动方式完成！')


# ============================================================
#  重命名工具函数
# ============================================================

def rename_output_files(directory: str, pattern: str = None):
    """
    批量重命名输出目录中的文件

    Args:
        directory: 目录路径
        pattern: 命名模式，支持 {index} {name} {ext} 等变量
    """
    if not os.path.isdir(directory):
        return

    files = sorted([f for f in os.listdir(directory)
                    if os.path.isfile(os.path.join(directory, f))])

    print(f'\n📝 目录 {directory} 中有 {len(files)} 个文件:')
    for i, f in enumerate(files, 1):
        print(f'   {i}. {f}')

    if pattern:
        print(f'\n🔄 按规则重命名: {pattern}')
        for i, f in enumerate(files, 1):
            name, ext = os.path.splitext(f)
            new_name = pattern.format(index=i, name=name, ext=ext)
            old_path = os.path.join(directory, f)
            new_path = os.path.join(directory, new_name)
            if old_path != new_path:
                os.rename(old_path, new_path)
                print(f'   {f} → {new_name}')


# ============================================================
#  主函数
# ============================================================

def main():
    print('\n' + '╔' + '═' * 58 + '╗')
    print('║' + ' ' * 15 + 'jmcomic 完整流程演示' + ' ' * 18 + '║')
    print('╚' + '═' * 58 + '╝')
    print()
    print('📋 配置信息:')
    print(f'   本子ID: {CONFIG["album_ids"]}')
    print(f'   客户端: {CONFIG["client_impl"]}')
    print(f'   下载目录: {os.path.abspath(CONFIG["download_dir"])}')
    print(f'   长图目录: {os.path.abspath(CONFIG["long_img_dir"])}')
    print(f'   长图命名: {CONFIG["long_img"]["filename_rule"]}')
    print()

    mode = 'feature'
    if len(sys.argv) > 1:
        mode = sys.argv[1]

    try:
        if mode == 'feature':
            run_with_feature(CONFIG)
        elif mode == 'plugin':
            run_with_plugin(CONFIG)
        elif mode == 'manual':
            run_manual(CONFIG)
        else:
            print(f'❌ 未知模式: {mode}')
            print('   可选: feature, plugin, manual')
            return

        # 列出输出文件
        long_img_dir = os.path.abspath(CONFIG['long_img_dir'])
        if os.path.isdir(long_img_dir):
            rename_output_files(long_img_dir)

    except Exception as e:
        print(f'\n❌ 运行出错: {e}')
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
