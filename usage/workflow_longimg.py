"""
GitHub Actions 增强版下载脚本：下载本子 → 转长图 → 重命名
"""
import os
from jmcomic import *


def env(name, default=''):
    value = os.getenv(name, default)
    if value is None or value == '':
        return default
    return value


def env_bool(name, default=False):
    val = env(name, '')
    if val == '':
        return default
    return str(val).lower() in ('true', '1', 'yes')


def str_to_set(text):
    return {
        s.strip()
        for s in text.replace('-', '\n').split('\n')
        if s.strip()
    }


def get_id_set(env_name, given=''):
    aid_set = set()
    for text in [given, env(env_name, '')]:
        aid_set.update(str_to_set(text))
    return aid_set


def build_option():
    download_dir = env('JM_DOWNLOAD_DIR', './download/')
    long_img_dir = env('LONG_IMG_DIR', './long_img/')
    mkdir_if_not_exists(download_dir)
    mkdir_if_not_exists(long_img_dir)

    option = JmModuleConfig.option_class().default()
    option.dir_rule = DirRule(
        rule='Bd_Aauthor_Atitle_Pindex',
        base_dir=download_dir,
    )

    impl = env('CLIENT_IMPL', 'api')
    option.client.impl = impl

    suffix = env('IMAGE_SUFFIX', '')
    if suffix:
        option.download.image.suffix = fix_suffix(suffix)

    username = env('JM_USERNAME', '')
    password = env('JM_PASSWORD', '')
    if username and password:
        option.plugins.setdefault('after_init', [])
        option.plugins['after_init'].append({
            'plugin': 'login',
            'kwargs': {
                'username': username,
                'password': password,
            }
        })

    long_img_enable = env_bool('LONG_IMG_ENABLE', True)
    long_img_level = env('LONG_IMG_LEVEL', 'album')
    long_img_name_rule = env('LONG_IMG_NAME_RULE', '[JM{Aid}]_{Atitle}')
    delete_original = env_bool('DELETE_ORIGINAL', True)

    if long_img_enable:
        call_when = 'after_album' if long_img_level == 'album' else 'after_photo'
        option.plugins.setdefault(call_when, [])
        option.plugins[call_when].append({
            'plugin': 'long_img',
            'kwargs': {
                'img_dir': long_img_dir,
                'filename_rule': long_img_name_rule,
                'delete_original_file': delete_original,
            }
        })

    return option


def main():
    album_id_set = get_id_set('JM_ALBUM_IDS')

    if not album_id_set:
        print('⚠️  没有指定本子ID，请设置 JM_ALBUM_IDS 环境变量')
        return

    print(f'📋 准备下载的本子ID: {album_id_set}')

    option = build_option()

    for aid in album_id_set:
        try:
            print(f'\n🚀 开始下载本子: {aid}')
            album, downloader = download_album(aid, option)
            print(f'✅ 本子 {aid} 处理完成')
        except Exception as e:
            print(f'❌ 本子 {aid} 处理失败: {e}')

    option.call_all_plugin('after_download')
    print('\n🎉 全部处理完成！')


if __name__ == '__main__':
    main()
