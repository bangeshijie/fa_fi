/**
 * 路由类型定义模块
 *
 * 提供路由相关的类型定义
 *
 * ## 主要功能
 *
 * - 路由元数据类型（标题、图标、权限等）
 * - 应用路由记录类型
 * - 菜单生成
 * - 动态路由
 * - 权限控制
 *
 * @module types/router/index
 */

import type { RouteRecordRaw } from "vue-router";
import "vue-router";
import type { Component } from "vue";

export type MenuType = 1 | 2 | 3 | 4;
/**
 * =========================================================
 * Vue Router RouteMeta 扩展
 * =========================================================
 */
declare module "vue-router" {

  interface RouteMeta {

    type?: MenuType;

    /** 菜单标题 */
    title?: string;

    /** 菜单图标 */
    icon?: string;

    /** 是否隐藏菜单 */
    hidden?: boolean;

    /** 是否始终显示父级菜单 */
    alwaysShow?: boolean;

    /** 是否固定标签页 */
    affix?: boolean;

    /** 是否缓存页面 */
    keepAlive?: boolean;

    /**
     * 是否使用 fullPath 作为 KeepAlive key
     *
     * true：
     * query/hash 变化也会重新创建组件
     */
    remountOnFullPath?: boolean;

    /**
     * 静态壳层路由
     *
     * 路由已经在 router 中注册，
     * 菜单项只负责跳转。
     */
    shellRoute?: boolean;

    /** 是否隐藏面包屑 */
    breadcrumb?: boolean;

  }
}


/**
 * =========================================================
 * 应用路由 Meta
 * =========================================================
 */
export interface AppRouteMeta
  extends Record<string | number | symbol, unknown> {

  /**
   * 菜单类型
   *
   * 1 = 目录
   * 2 = 菜单
   * 3 = 权限
   * 4 = 外链
   */
  type?: MenuType;

  /** 路由标题 */
  title: string;

  /** 菜单图标 */
  icon?: string;

  /** 是否显示徽章 */
  showBadge?: boolean;

  /** 文本徽章 */
  showTextBadge?: string;

  /** 是否隐藏菜单 */
  hidden?: boolean;

  /** 是否隐藏标签页 */
  isHideTab?: boolean;

  /** 外部链接 */
  link?: string;

  /** 是否 iframe */
  isIframe?: boolean;

  /** 是否缓存 */
  keepAlive?: boolean;

  /**
   * 操作权限列表
   *
   * 例如：
   *
   * [
   *   {
   *     title: "新增",
   *     authMark: "module_system:menu:create"
   *   }
   * ]
   */
  authList?: Array<{
    title: string;
    authMark: string;
  }>;

  /** 是否一级菜单 */
  isFirstLevel?: boolean;

  /** 角色权限 */
  roles?: string[];

  /** 是否固定标签页 */
  fixedTab?: boolean;

  /** 激活菜单路径 */
  activePath?: string;

  /** 是否权限按钮 */
  isAuthButton?: boolean;

  /**
   * 权限标识
   *
   * 一般对应菜单 type=3 的 permission
   */
  authMark?: string;

  /** 父级路径 */
  parentPath?: string;

  /** 静态壳层菜单 */
  shellRoute?: boolean;

  /**
   * 是否使用 fullPath 作为缓存 key
   */
  remountOnFullPath?: boolean;
  /** 是否外链 */
external?: boolean;

/** 路由参数 */
params?: Array<{
    key: string;
    value: string;
}>;
}


/**
 * =========================================================
 * 应用路由记录
 * =========================================================
 */
export interface AppRouteRecord
  extends Omit<
    RouteRecordRaw,
    "children" | "component"
  > {

  /** 菜单 ID */
  id?: number;

  /** 路由元数据 */
  meta: AppRouteMeta;

  /** 页面组件 */
  component?: Component;

  /** 子路由 */
  children?: AppRouteRecord[];
}