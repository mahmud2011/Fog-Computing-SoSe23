package com.example.demo.dto

import com.example.demo.model.ConfigEntity
import com.example.demo.model.EdgeDataEntity
import com.fasterxml.jackson.annotation.JsonIgnore

data class ConfigDTO (
    var data: Map<String, Any>,
    var id: Long? = null,
    var edgeId: Long) {
    fun toConfigEntity(edgeDataRecord: EdgeDataEntity): ConfigEntity {
        return ConfigEntity(data = data).apply { edgeData = edgeDataRecord }
    }
}