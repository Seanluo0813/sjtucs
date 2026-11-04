# 知径 · CS2023 学科导航

交互式计算机科学知识导航：17 个知识领域、162 个知识单元、50 门交大课程学习入口。

## GitHub Pages 部署

将本目录上传到 GitHub 仓库的 main 分支，在 Settings → Pages → Build and deployment 中选择 GitHub Actions。推送后，工作流校验网站并发布 dist/。

项目网站地址由 GitHub Pages 部署结果确定。所有资源使用相对路径，支持仓库子路径部署。

## 本地验证

```sh
python3 src/check_site.py --root dist
```

网页文件在 dist/；数据与素材来源见 dist/sources.md 和 dist/assets/ASSET_SOURCES.md。

自定义域名 sjtucs.lc.site 尚未完成 DNS 验证，本项目未配置 CNAME 文件。
