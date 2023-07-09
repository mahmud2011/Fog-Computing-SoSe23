package com.example.demo.model

import com.fasterxml.jackson.annotation.JsonBackReference
import io.hypersistence.utils.hibernate.type.json.JsonType
import jakarta.persistence.*
import jakarta.persistence.GenerationType.IDENTITY
import org.hibernate.annotations.Type

@Entity
@Table(name = "edge_data", schema = "demo")
class EdgeDataEntity (
    @Id
    @GeneratedValue(strategy = IDENTITY)
    @Column(name = "id", nullable = false)
    val id: Long? = 0,

    @Type(JsonType::class)
    @Column(columnDefinition = "jsonb")
    var data: Map<String, Any>? = null
) {
    @ManyToOne
    @JoinColumn(name="user_token_id", nullable=false)
    @JsonBackReference
    var userToken: UserTokenEntity? = null
}