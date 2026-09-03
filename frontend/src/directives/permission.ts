import type { Directive } from "vue";

import pinia from "@/store";
import { useAuthStore } from "@/store/auth";

export type PermissionValue =
    | string
    | string[];

export function hasPermission(
    value: PermissionValue
): boolean {
    const authStore =
        useAuthStore(pinia);

    if (
        authStore.info?.is_superuser === true
    ) {
        return true;
    }

    const permissions =
        authStore.prems;

    if (
        typeof value === "string"
    ) {
        return permissions.includes(value);
    }

    if (
        Array.isArray(value)
    ) {
        return value.some(
            permission =>
                permissions.includes(permission)
        );
    }

    return false;
}

const permissionDirective:
    Directive<
        HTMLElement,
        PermissionValue
    > = {
        mounted(el, binding) {
            if (
                !hasPermission(
                    binding.value
                )
            ) {
                el.remove();
            }
        },
    };

export default permissionDirective;